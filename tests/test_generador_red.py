import math

from src.generador_red import generar_red


def _construir_estructura_comparable(G):
    """Convierte el grafo en dicts/sets simples, fáciles de comparar en los asserts."""
    nodos = {nodo: dict(datos) for nodo, datos in G.nodes(data=True)}
    aristas = {frozenset((u, v)): datos["weight"] for u, v, datos in G.edges(data=True)}
    return nodos, aristas


def test_misma_seed_genera_el_mismo_grafo():
    params = dict(num_serv=3, num_usr=5, capacidad_max=6, radio_cobertura=40, seed=7, lado_area=100)

    G1, serv1, usr1 = generar_red(**params)
    G2, serv2, usr2 = generar_red(**params)

    assert serv1 == serv2
    assert usr1 == usr2

    nodos1, aristas1 = _construir_estructura_comparable(G1)
    nodos2, aristas2 = _construir_estructura_comparable(G2)

    assert nodos1 == nodos2
    assert aristas1 == aristas2


def test_usuarios_y_servidores_tienen_atributos_validos(red_pequena_ok):
    G, servidores, usuarios = red_pequena_ok

    for usuario in usuarios:
        datos = G.nodes[usuario]
        assert datos["tipo"] == "usuario"
        assert 1 <= datos["demanda"] <= 3
        assert "pos" in datos

    for servidor in servidores:
        datos = G.nodes[servidor]
        assert datos["tipo"] == "servidor"
        assert "capacidad" in datos
        assert "pos" in datos


def test_usuario_se_conecta_al_menos_al_servidor_mas_cercano_aunque_este_fuera_de_cobertura():
    # Con un radio de cobertura minúsculo, en la práctica ningún usuario entra en rango
    # salvo por pura casualidad: así comprobamos que el fallback de generador_red.py
    # (conectar siempre con el servidor más cercano) sigue funcionando.
    G, servidores, usuarios = generar_red(
        num_serv=4, num_usr=6, capacidad_max=6, radio_cobertura=0.001, seed=13, lado_area=100
    )

    for usuario in usuarios:
        pos_u = G.nodes[usuario]["pos"]
        servidor_mas_cercano = min(servidores, key=lambda s: math.dist(pos_u, G.nodes[s]["pos"]))
        assert G.has_edge(usuario, servidor_mas_cercano)


def test_cambiar_lado_area_cambia_el_rango_de_coordenadas():
    G_pequena, _, _ = generar_red(num_serv=3, num_usr=5, capacidad_max=6, radio_cobertura=40, seed=7, lado_area=10)
    G_grande, _, _ = generar_red(num_serv=3, num_usr=5, capacidad_max=6, radio_cobertura=40, seed=7, lado_area=1000)

    coords_pequena = [c for _, datos in G_pequena.nodes(data=True) for c in datos["pos"]]
    coords_grande = [c for _, datos in G_grande.nodes(data=True) for c in datos["pos"]]

    assert max(coords_pequena) <= 10
    assert max(coords_grande) <= 1000
    assert max(coords_grande) > max(coords_pequena)
