"""
Esto lo llama benchmark.py como subproceso aparte, uno por cada ejecución.

Regenera la red con la misma semilla y ejecuta un solver, y al final imprime el
resultado en JSON en la última línea de la salida. Va en su propio proceso para
que si un solver se atasca (CBC dando vueltas, QAOA sin converger) se pueda matar
con un timeout sin cargarse el kernel del notebook.
"""
import json
import sys
import time

from src.generador_red import generar_red


def _cargar_solver(nombre):
    if nombre == "voraz":
        from src.solver_voraz import solver_voraz as fn
    elif nombre == "exacto":
        from src.solver_exacto import solver_exacto as fn
    elif nombre == "cuantico":
        from src.solver_cuantico import solver_cuantico as fn
    else:
        raise ValueError(f"Solver desconocido: {nombre}")
    return fn


def main():
    solver_nombre, num_serv, num_usr, capacidad_max, radio_cobertura, seed, lado_area = sys.argv[1:8]

    G, servidores, usuarios = generar_red(
        num_serv=int(num_serv),
        num_usr=int(num_usr),
        capacidad_max=int(capacidad_max),
        radio_cobertura=float(radio_cobertura),
        seed=int(seed),
        lado_area=int(lado_area),
    )

    solver_fn = _cargar_solver(solver_nombre)

    t0 = time.perf_counter()
    asignaciones, latencia = solver_fn(G, servidores, usuarios)
    tiempo = time.perf_counter() - t0

    resultado = {
        "tiempo": tiempo,
        "latencia": latencia,
        "sin_asignar": len(usuarios) - len(asignaciones),
    }
    print(json.dumps(resultado))


if __name__ == "__main__":
    main()
