import json
import os
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import pandas as pd

from src.generador_red import generar_red

LIMITE_QUBITS = 20
RAIZ_PROYECTO = Path(__file__).resolve().parent.parent


def _estimar_qubits_base(G, lista_usuarios):
    """Es el mismo cálculo que ya hace solver_cuantico.py: usuarios × servidores alcanzables + usuarios."""
    return sum(len(G[u]) for u in lista_usuarios) + len(lista_usuarios)


def _ejecutar_solver_aislado(solver_nombre, num_servidores, tamanio, capacidad_max, radio_cobertura, seed, timeout_s, lado_area):
    """
    Lanza un solver en un proceso aparte con un tiempo límite, para que si se atasca
    (CBC dando vueltas, QAOA sin converger...) no se nos cuelgue todo el benchmark.
    Si se pasa del tiempo devolvemos None y seguimos con el siguiente.
    """
    comando = [
        sys.executable, "-m", "src._benchmark_worker",
        solver_nombre, str(num_servidores), str(tamanio), str(capacidad_max), str(radio_cobertura), str(seed),
        str(lado_area),
    ]
    proceso = subprocess.Popen(
        comando, cwd=RAIZ_PROYECTO, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
    )
    try:
        stdout, _ = proceso.communicate(timeout=timeout_s)
    except subprocess.TimeoutExpired:
        # En Windows no basta con matar el proceso worker: sus hijos (como el cbc.exe que lanza PuLP) se quedan vivos, así que hay que matar todo el árbol de procesos.
        subprocess.run(["taskkill", "/F", "/T", "/PID", str(proceso.pid)], capture_output=True)
        proceso.wait()
        print(f"[benchmark] {solver_nombre} (tamanio={tamanio}, seed={seed}) superó el timeout de {timeout_s}s -> NaN")
        return None

    lineas = [l for l in stdout.strip().splitlines() if l.strip()]
    if proceso.returncode != 0 or not lineas:
        print(f"[benchmark] {solver_nombre} (tamanio={tamanio}, seed={seed}) falló (código {proceso.returncode}) -> NaN")
        return None

    return json.loads(lineas[-1])


def ejecutar_benchmark_escalabilidad(
    tamanios_usuarios, num_servidores, capacidad_max, radio_cobertura,
    repeticiones=5, timeout_s=60, max_workers=None, lado_area=100,
):
    """
    Mide tiempo, latencia total y usuarios sin asignar de los tres solvers para cada
    tamaño de red que le pasemos, repitiendo cada tamaño varias veces (con redes
    distintas) y promediando.

    num_servidores puede ser un número fijo o una función tamanio -> num_servidores,
    para que el número de servidores crezca junto con los usuarios en vez de dejar la
    red saturada con pocos servidores fijos.

    lado_area funciona igual (número fijo o función) y sirve para que el mapa crezca a
    la vez que la red, así la densidad de servidores por área no cambia con el tamaño.
    Si dejamos el mapa fijo mientras la red crece, la red se vuelve más fácil o más
    difícil sin querer, solo por cómo hemos montado el experimento, no por el tamaño
    en sí.

    Cada ejecución tiene un timeout de timeout_s segundos: si lo supera cuenta como
    NaN pero seguimos con el resto. Al solver cuántico directamente no lo intentamos
    si el número de variables base supera LIMITE_QUBITS.

    Las repeticiones de un mismo tamaño y los solvers de una misma repetición son
    independientes entre sí, así que las lanzamos en paralelo con un
    ThreadPoolExecutor. Ojo, esto no es el típico paralelismo falso de Python limitado
    por el GIL: cada hilo se pasa casi todo el rato esperando bloqueado en
    Popen(...).communicate(...), y esa espera libera el GIL. El trabajo de verdad
    (CBC, QAOA, el propio voraz) lo hacen procesos aparte del sistema operativo, cada
    uno en su propio núcleo — los hilos de aquí solo esperan, no calculan.
    """
    if max_workers is None:
        max_workers = max(1, (os.cpu_count() or 4) - 1)

    # Primero montamos la lista de tareas (tamaño, repetición, solver, seed).
    # Estimar los qubits solo implica regenerar el grafo, que es barato y no resuelve
    # nada, así que esto lo hacemos aquí en secuencia sin paralelizar.
    tareas = []
    qubits_por_tamanio_rep = {}
    servidores_por_tamanio = {}

    for tamanio in tamanios_usuarios:
        servers_tamanio = num_servidores(tamanio) if callable(num_servidores) else num_servidores
        servidores_por_tamanio[tamanio] = servers_tamanio
        lado_area_tamanio = round(lado_area(tamanio) if callable(lado_area) else lado_area)

        for i in range(repeticiones):
            seed = tamanio * 100 + i

            G, servidores, usuarios = generar_red(
                num_serv=servers_tamanio, num_usr=tamanio,
                capacidad_max=capacidad_max, radio_cobertura=radio_cobertura, seed=seed,
                lado_area=lado_area_tamanio,
            )
            num_qubits = _estimar_qubits_base(G, usuarios)
            qubits_por_tamanio_rep[(tamanio, i)] = num_qubits

            for solver_nombre in ("voraz", "exacto"):
                tareas.append((tamanio, i, solver_nombre, seed, servers_tamanio, lado_area_tamanio))
            if num_qubits <= LIMITE_QUBITS:
                tareas.append((tamanio, i, "cuantico", seed, servers_tamanio, lado_area_tamanio))

    # Guardamos cada resultado con su clave (tamanio, repeticion, solver), así que
    # aunque terminen en un orden distinto al que los lanzamos, no se nos mezclan las
    # métricas de una repetición con las de otra.
    resultados = {}
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futuros = {
            executor.submit(
                _ejecutar_solver_aislado, solver_nombre, servers_tamanio, tamanio,
                capacidad_max, radio_cobertura, seed, timeout_s, lado_area_tamanio,
            ): (tamanio, i, solver_nombre)
            for (tamanio, i, solver_nombre, seed, servers_tamanio, lado_area_tamanio) in tareas
        }
        for futuro in as_completed(futuros):
            clave = futuros[futuro]
            resultados[clave] = futuro.result()

    filas = []
    for tamanio in tamanios_usuarios:
        metricas = {
            "voraz": {"tiempo": [], "latencia": [], "sin_asignar": []},
            "exacto": {"tiempo": [], "latencia": [], "sin_asignar": []},
            "cuantico": {"tiempo": [], "latencia": [], "sin_asignar": []},
        }

        for i in range(repeticiones):
            for solver_nombre in ("voraz", "exacto", "cuantico"):
                resultado = resultados.get((tamanio, i, solver_nombre))
                if resultado is not None:
                    metricas[solver_nombre]["tiempo"].append(resultado["tiempo"])
                    metricas[solver_nombre]["latencia"].append(resultado["latencia"])
                    metricas[solver_nombre]["sin_asignar"].append(resultado["sin_asignar"])

        qubits_por_repeticion = [qubits_por_tamanio_rep[(tamanio, i)] for i in range(repeticiones)]
        num_qubits_medio = sum(qubits_por_repeticion) / len(qubits_por_repeticion)

        for solver, datos in metricas.items():
            n = len(datos["tiempo"])
            filas.append({
                "tamanio": tamanio,
                "num_servidores": servidores_por_tamanio[tamanio],
                "solver": solver,
                "tiempo_medio_s": sum(datos["tiempo"]) / n if n else float("nan"),
                "latencia_media": sum(datos["latencia"]) / n if n else float("nan"),
                "usuarios_sin_asignar_media": sum(datos["sin_asignar"]) / n if n else float("nan"),
                "num_qubits_estimado": num_qubits_medio,
            })

    return pd.DataFrame(filas)
