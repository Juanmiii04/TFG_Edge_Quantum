import pytest

from src.generador_red import generar_red
from src.solver_cuantico import construir_qubo, solver_cuantico


def test_construccion_del_qubo_para_una_red_minima():
    # 1 servidor y 2 usuarios: con un único servidor ambos quedan conectados
    # a él siempre (fallback del servidor más cercano), así que sabemos de
    # antemano cuántas variables y restricciones debería tener el modelo.
    #
    # Usamos construir_qubo(...) directamente -- la misma función que usa
    # solver_cuantico por dentro, en vez de reconstruir el modelado a mano --
    # para que este test detecte de verdad cualquier cambio futuro en el
    # modelo (una restricción nueva, por ejemplo) sin pagar el coste de
    # montar y ejecutar QAOA.
    G, servidores, usuarios = generar_red(
        num_serv=1, num_usr=2, capacidad_max=3, radio_cobertura=200, seed=5, lado_area=50
    )

    qp, x_vars, y_vars = construir_qubo(G, servidores, usuarios)

    # 2 variables x_u_s (una por usuario, ya que solo hay un servidor) + 2 variables y_u
    assert qp.get_num_vars() == 4
    assert len(x_vars) == 2
    assert len(y_vars) == 2
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
