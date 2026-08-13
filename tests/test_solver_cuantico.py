import pytest
from qiskit_optimization import QuadraticProgram

from src.generador_red import generar_red
from src.solver_cuantico import solver_cuantico

# Mismo valor que usa internamente solver_cuantico (constante duplicada, no
# centralizada -- ver CLAUDE.md).
PENALIZACION = 1000


def _construir_quadratic_program(G, servidores, usuarios):
    """
    Reconstruye solo la parte de modelado (variables y restricciones) de
    solver_cuantico.py, sin llegar a configurar ni ejecutar QAOA. Así
    podemos comprobar el tamaño del QUBO en un test rápido, sin pagar el
    coste de la simulación cuántica.
    """
    qp = QuadraticProgram("Balanceo_Edge_Cuantico_Test")

    x_vars = {}
    for u in usuarios:
        for s in G[u]:
            var_name = f"x_{u}_{s}"
            qp.binary_var(name=var_name)
            x_vars[(u, s)] = var_name

    y_vars = {}
    for u in usuarios:
        var_name = f"y_{u}"
        qp.binary_var(name=var_name)
        y_vars[u] = var_name

    obj_linear = {}
    for u in usuarios:
        for s in G[u]:
            obj_linear[x_vars[(u, s)]] = G[u][s]["weight"]
        obj_linear[y_vars[u]] = PENALIZACION
    qp.minimize(linear=obj_linear)

    for u in usuarios:
        lin_dict = {x_vars[(u, s)]: 1 for s in G[u]}
        lin_dict[y_vars[u]] = 1
        qp.linear_constraint(linear=lin_dict, sense="==", rhs=1, name=f"Asignacion_{u}")

    for s in servidores:
        lin_dict = {}
        for u in usuarios:
            if s in G[u]:
                lin_dict[x_vars[(u, s)]] = G.nodes[u].get("demanda", 1)
        qp.linear_constraint(linear=lin_dict, sense="<=", rhs=G.nodes[s]["capacidad"], name=f"Capacidad_{s}")

    return qp


def test_construccion_del_qubo_para_una_red_minima():
    # 1 servidor y 2 usuarios: con un único servidor ambos quedan conectados
    # a él siempre (fallback del servidor más cercano), así que sabemos de
    # antemano cuántas variables y restricciones debería tener el modelo.
    G, servidores, usuarios = generar_red(
        num_serv=1, num_usr=2, capacidad_max=3, radio_cobertura=200, seed=5, lado_area=50
    )

    qp = _construir_quadratic_program(G, servidores, usuarios)

    # 2 variables x_u_s (una por usuario, ya que solo hay un servidor) + 2 variables y_u
    assert qp.get_num_vars() == 4
    # 2 restricciones de "asignación única o desconexión" (una por usuario) + 1 de capacidad (un servidor)
    assert qp.get_num_linear_constraints() == 3


@pytest.mark.slow
def test_solver_cuantico_ejecuta_qaoa_sobre_red_minima():
    # Test lento de verdad: ejecuta QAOA completo. Solo comprobamos que no
    # falla y que el formato de salida es correcto -- QAOA es estocástico y
    # no tiene por qué converger al óptimo, así que no comparamos con el
    # voraz/exacto ni comprobamos optimalidad.
    G, servidores, usuarios = generar_red(
        num_serv=1, num_usr=2, capacidad_max=3, radio_cobertura=200, seed=5, lado_area=50
    )

    asignaciones, latencia_total = solver_cuantico(G, servidores, usuarios)

    assert isinstance(asignaciones, dict)
    for usuario, (servidor, latencia) in asignaciones.items():
        assert usuario in usuarios
        assert servidor in servidores
        assert isinstance(latencia, (int, float))

    assert isinstance(latencia_total, (int, float))
    assert latencia_total >= 0
    assert latencia_total != float("inf")
