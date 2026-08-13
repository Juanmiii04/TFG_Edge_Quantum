import numpy as np
import time
import warnings

from qiskit_optimization import QuadraticProgram
from qiskit_optimization.algorithms import MinimumEigenOptimizer
from qiskit_algorithms import QAOA
from qiskit_algorithms.optimizers import COBYLA
from qiskit.primitives import StatevectorSampler

from src.constantes import PENALIZACION

warnings.filterwarnings('ignore') # Ocultar avisos internos de qiskit


def construir_qubo(G, lista_servidores, lista_usuarios):
    """
    Construye el QuadraticProgram del modelo de balanceo de carga (variables, función
    objetivo y restricciones), sin llegar a resolverlo. Separado de solver_cuantico
    para que tanto el solver como los tests usen exactamente la misma construcción del
    modelo -- si el modelo cambia (se añade una restricción, por ejemplo), no hay una
    copia duplicada en los tests que se pueda quedar desactualizada sin que salte nada.

    Devuelve (qp, x_vars, y_vars): x_vars/y_vars hacen falta después para traducir el
    resultado de QAOA (valores 0/1 por variable) de vuelta a asignaciones usuario ->
    servidor.
    """
    qp = QuadraticProgram("Balanceo_Edge_Cuantico")

    #Variables de decisión(cada posible decisión equivale a un qubit)
    x_vars = {} #vale 1 si se asigna a un servidor s
    for u in lista_usuarios:
        for s in G[u]:
            var_name = f"x_{u}_{s}"
            qp.binary_var(name=var_name)
            x_vars[(u, s)] = var_name

    y_vars = {} #vale 1 si no tiene sitio en un servidor
    for u in lista_usuarios:
        var_name = f"y_{u}"
        qp.binary_var(name=var_name)
        y_vars[u] = var_name

    #Función Objetivo(misma idea que con el solver exacto, pero con  Qiskit-Optimization la librería de traducción matemática de IBM)
    obj_linear = {}
    for u in lista_usuarios:
        for s in G[u]:
            obj_linear[x_vars[(u, s)]] = G[u][s]['weight'] #asignamos la latencia a cada una de las variables de decisión
        obj_linear[y_vars[u]] = PENALIZACION #si un usuario no se conecta a ningún servidor

    qp.minimize(linear=obj_linear)

    #Restricción 1 -> Asignación Única o Desconexión
    for u in lista_usuarios:
        lin_dict = {x_vars[(u, s)]: 1 for s in G[u]}
        lin_dict[y_vars[u]] = 1
        qp.linear_constraint(linear=lin_dict, sense='==', rhs=1, name=f"Asignacion_{u}")

    #Restricción 2 -> Capacidad de los servidores
    for s in lista_servidores:
        lin_dict = {}
        for u in lista_usuarios:
            if s in G[u]:
                lin_dict[x_vars[(u, s)]] = G.nodes[u].get('demanda', 1)
        qp.linear_constraint(linear=lin_dict, sense='<=', rhs=G.nodes[s]['capacidad'], name=f"Capacidad_{s}")

    return qp, x_vars, y_vars


def solver_cuantico(G, lista_servidores, lista_usuarios, backend='simulador'):
    """
    Con backend='simulador' se simula el circuito en local(los qubits los genera el propio ordenador) con
    StatevectorSampler. Con backend='ibm_real' se ejecuta en un ordenador cuántico
    real de IBM a través de qiskit-ibm-runtime — para esto hace falta haber guardado
    antes tus credenciales con QiskitRuntimeService.save_account(...); el token no se
    lee ni se escribe en ningún sitio de este archivo, por lo que es privado.
    """
    print("Iniciamos algoritmo cuántico (QAOA con Qiskit):")

    #Creamos el modelo matemático (muy similar al solver exacto)
    qp, x_vars, y_vars = construir_qubo(G, lista_servidores, lista_usuarios)

    num_vars = qp.get_num_vars()
    print(f" -> Construyendo QUBO con {num_vars} variables cuánticas (qubits base).")

    #a nuestro ordenador le cuesta mucho similar qubits, por eso tenemos que tener cuidado
    if num_vars > 20:
        print("\n Cuidado estás intentando simular más de 20 qubits")
        print(" Esto puede consumir muchos recursos de tu PC y tardar horas")
        print(" Para pruebas cuánticas iniciales recomendamos: 1-2 Servidores y 2-4 Usuarios.\n")

    # 6. Configurar QAOA (Mejoras V2 aplicadas)
    print(" -> Configurando Optimizador QAOA y Sampler V2...")
    optimizer_clasico = COBYLA(maxiter=300, disp=True)

    if backend == 'simulador':
        sampler_v2 = StatevectorSampler()
    elif backend == 'ibm_real':
        # Lo importamos aquí dentro y no arriba del todo, para no depender de
        # qiskit-ibm-runtime si al final no vamos a usar hardware real.
        from qiskit_ibm_runtime import QiskitRuntimeService
        from qiskit_ibm_runtime import SamplerV2 as IBMRuntimeSampler

        servicio = QiskitRuntimeService()  # coge las credenciales que ya tengas guardadas con save_account(...)
        backend_real = servicio.least_busy(min_num_qubits=num_vars)
        print(f" -> Backend real de IBM seleccionado: {backend_real.name}")
        sampler_v2 = IBMRuntimeSampler(mode=backend_real)
    else:
        raise ValueError(f"backend desconocido: {backend!r}. Usa 'simulador' o 'ibm_real'.")

    qaoa_mes = QAOA(
        sampler=sampler_v2, 
        optimizer=optimizer_clasico, 
        reps=2 
    )
    optimizer = MinimumEigenOptimizer(qaoa_mes)
    
    print(" -> Ejecutando simulación cuántica (esto puede tardar unos minutos)...")
    start_time = time.time()
    
    # 7. Resolver
    try:
        result = optimizer.solve(qp)
    except Exception as e:
        print(f"\n [ERROR] Fallo en simulación. Revisa la RAM o reduce los qubits: {e}")
        return {}, 0
        
    end_time = time.time()
    print(f" -> Simulación finalizada en {round(end_time - start_time, 2)} segundos.")
    
    # 8. Procesar resultados
    asignaciones = {}
    latencia_asignada = 0
    ocupacion_servidores = {s: 0 for s in lista_servidores}
    usuarios_sin_asignar = []
    
    for u in lista_usuarios:
        if result.variables_dict[y_vars[u]] > 0.5:
            usuarios_sin_asignar.append(u)
        else:
            for s in G[u]:
                if result.variables_dict[x_vars[(u, s)]] > 0.5:
                    latencia = G[u][s]['weight']
                    demanda = G.nodes[u].get('demanda', 1)
                    
                    asignaciones[u] = (s, latencia)
                    latencia_asignada += latencia
                    ocupacion_servidores[s] += demanda
                    
    latencia_penalizacion = len(usuarios_sin_asignar) * PENALIZACION
    latencia_total = latencia_asignada + latencia_penalizacion
    
    # 9. Imprimir resultados
    for servidor in lista_servidores:
        usuarios_este_servidor = [
            f"{u} ({asignaciones[u][1]}ms, dem: {G.nodes[u].get('demanda', 1)})" 
            for u in asignaciones if asignaciones[u][0] == servidor
        ]
        print(f" {servidor} (Ocupación recursos: {ocupacion_servidores[servidor]}/{G.nodes[servidor]['capacidad']}): {', '.join(usuarios_este_servidor)}")
        
    print(f"\n Latencia total de la red (Cuántico QAOA): {latencia_total} ms")
    if usuarios_sin_asignar:
        print(f" -> Detalle: {latencia_asignada} ms (Asignados) + {latencia_penalizacion} ms (Penalización por {len(usuarios_sin_asignar)} desconectados)")
        print(f" Usuarios desconectados: {', '.join(usuarios_sin_asignar)}")
    print("------------------------------------------")
    
    return asignaciones, latencia_total

