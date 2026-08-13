from src.gestor_redes import cargar_red, guardar_red
from src.generador_red import generar_red


def _construir_estructura_comparable(G):
    """Igual que en test_generador_red.py, pero normalizando 'pos' a tupla:
    tras pasar por JSON, las tuplas de posición vuelven como listas."""
    nodos = {}
    for nodo, datos in G.nodes(data=True):
        datos_normalizados = dict(datos)
        if "pos" in datos_normalizados:
            datos_normalizados["pos"] = tuple(datos_normalizados["pos"])
        nodos[nodo] = datos_normalizados

    aristas = {frozenset((u, v)): datos["weight"] for u, v, datos in G.edges(data=True)}
    return nodos, aristas


def test_guardar_y_cargar_red_devuelve_un_grafo_equivalente(tmp_path):
    G_original, servidores_original, usuarios_original = generar_red(
        num_serv=3, num_usr=5, capacidad_max=6, radio_cobertura=40, seed=21, lado_area=100
    )

    filepath = tmp_path / "red_test.json"
    guardar_red(G_original, servidores_original, usuarios_original, filepath=str(filepath))

    G_cargado, servidores_cargado, usuarios_cargado = cargar_red(filepath=str(filepath))

    assert servidores_cargado == servidores_original
    assert usuarios_cargado == usuarios_original

    nodos_original, aristas_original = _construir_estructura_comparable(G_original)
    nodos_cargado, aristas_cargado = _construir_estructura_comparable(G_cargado)

    assert nodos_cargado == nodos_original
    assert aristas_cargado == aristas_original
