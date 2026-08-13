import itertools

from src.constantes import PENALIZACION
from src.generador_red import generar_red
from src.solver_exacto import solver_exacto


def _mejor_latencia_por_fuerza_bruta(G, servidores, usuarios):
    """
    Prueba a mano todas las asignaciones posibles (incluida la opción de
    dejar a un usuario sin conectar) y se queda con la de menor latencia,
    respetando la capacidad de cada servidor. Sirve como oráculo independiente
    para comprobar que PuLP encuentra de verdad el óptimo.
    """
    opciones_por_usuario = [list(G[usuario]) + [None] for usuario in usuarios]

    mejor_latencia = None

    for combinacion in itertools.product(*opciones_por_usuario):
        ocupacion = {s: 0 for s in servidores}
        latencia_total = 0
        valido = True

        for usuario, servidor in zip(usuarios, combinacion):
            if servidor is None:
                latencia_total += PENALIZACION
                continue

            demanda = G.nodes[usuario]["demanda"]
            ocupacion[servidor] += demanda
            if ocupacion[servidor] > G.nodes[servidor]["capacidad"]:
                valido = False
                break

            latencia_total += G[usuario][servidor]["weight"]

        if not valido:
            continue

        if mejor_latencia is None or latencia_total < mejor_latencia:
            mejor_latencia = latencia_total

    return mejor_latencia


def test_solver_exacto_encuentra_el_optimo_real():
    # Red deliberadamente pequeña (3 servidores, 4 usuarios) para que la
    # fuerza bruta sea viable como comparación independiente.
    G, servidores, usuarios = generar_red(
        num_serv=3, num_usr=4, capacidad_max=3, radio_cobertura=200, seed=99, lado_area=50
    )

    _asignaciones, latencia_exacto = solver_exacto(G, servidores, usuarios)
    latencia_fuerza_bruta = _mejor_latencia_por_fuerza_bruta(G, servidores, usuarios)

    assert latencia_exacto == latencia_fuerza_bruta
