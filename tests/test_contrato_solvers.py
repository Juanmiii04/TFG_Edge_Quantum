import pytest

from src.constantes import PENALIZACION
from src.solver_exacto import solver_exacto
from src.solver_voraz import solver_voraz

SOLVERS = [solver_voraz, solver_exacto]


@pytest.mark.parametrize("solver", SOLVERS)
def test_formato_resultado(solver, red_pequena_ok):
    G, servidores, usuarios = red_pequena_ok

    asignaciones, latencia_total = solver(G, servidores, usuarios)

    assert isinstance(asignaciones, dict)
    assert isinstance(latencia_total, (int, float))

    for usuario, (servidor, latencia) in asignaciones.items():
        assert usuario in usuarios
        assert servidor in servidores
        assert isinstance(latencia, (int, float))


@pytest.mark.parametrize("solver", SOLVERS)
@pytest.mark.parametrize("nombre_fixture_red", ["red_pequena_ok", "red_pequena_sobrecargada"])
def test_no_se_supera_la_capacidad_de_ningun_servidor(solver, nombre_fixture_red, request):
    # Con red_pequena_ok la capacidad va tan sobrada que casi cualquier asignación la
    # respeta, incluso una mal calculada -- así que también se prueba con
    # red_pequena_sobrecargada (capacidad=1), donde de verdad se roza el límite y un
    # bug real en la comprobación de hueco (contar servidores, no ocupación) se
    # detecta.
    G, servidores, usuarios = request.getfixturevalue(nombre_fixture_red)

    asignaciones, _latencia_total = solver(G, servidores, usuarios)

    ocupacion = {s: 0 for s in servidores}
    for usuario, (servidor, _latencia) in asignaciones.items():
        ocupacion[servidor] += G.nodes[usuario]["demanda"]

    for servidor in servidores:
        assert ocupacion[servidor] <= G.nodes[servidor]["capacidad"]


@pytest.mark.parametrize("solver", SOLVERS)
def test_latencia_total_incluye_penalizacion_por_usuarios_sin_asignar(solver, red_pequena_sobrecargada):
    G, servidores, usuarios = red_pequena_sobrecargada

    asignaciones, latencia_total = solver(G, servidores, usuarios)

    usuarios_sin_asignar = [u for u in usuarios if u not in asignaciones]
    latencia_asignada = sum(latencia for _servidor, latencia in asignaciones.values())
    latencia_esperada = latencia_asignada + len(usuarios_sin_asignar) * PENALIZACION

    assert latencia_total == latencia_esperada


@pytest.mark.parametrize("solver", SOLVERS)
def test_red_sobrecargada_deja_al_menos_un_usuario_sin_asignar(solver, red_pequena_sobrecargada):
    G, servidores, usuarios = red_pequena_sobrecargada

    asignaciones, _latencia_total = solver(G, servidores, usuarios)

    usuarios_sin_asignar = [u for u in usuarios if u not in asignaciones]
    assert len(usuarios_sin_asignar) >= 1


def test_el_exacto_nunca_es_peor_que_el_voraz(red_pequena_ok):
    # El exacto resuelve el MILP de forma óptima, así que en la misma red
    # nunca puede quedar por encima de lo que consigue el voraz.
    G, servidores, usuarios = red_pequena_ok

    _asignaciones_voraz, latencia_voraz = solver_voraz(G, servidores, usuarios)
    _asignaciones_exacto, latencia_exacto = solver_exacto(G, servidores, usuarios)

    assert latencia_exacto <= latencia_voraz
