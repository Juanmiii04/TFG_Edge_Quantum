import networkx as nx

from src.solver_voraz import solver_voraz


def test_no_lanza_nameerror_cuando_todos_los_usuarios_caben(red_pequena_ok):
    # Regresión del bug donde num_desc/texto_desc estaban mal indentados
    # (se usaban fuera del "if usuarios_sin_asignar:") y provocaban un
    # NameError en cuanto no quedaba ningún usuario desconectado.
    G, servidores, usuarios = red_pequena_ok

    asignaciones, latencia_total = solver_voraz(G, servidores, usuarios)

    assert len(asignaciones) == len(usuarios)
    assert latencia_total >= 0


def _construir_red_manual(aristas, capacidades, demandas):
    """
    Crea una red mínima a mano (sin generador_red) para controlar con
    precisión latencias, capacidades y demandas en cada test.

    aristas: lista de tuplas (usuario, servidor, latencia)
    capacidades: dict servidor -> capacidad
    demandas: dict usuario -> demanda
    """
    G = nx.Graph()
    for servidor, capacidad in capacidades.items():
        G.add_node(servidor, tipo="servidor", capacidad=capacidad, pos=(0, 0))
    for usuario, demanda in demandas.items():
        G.add_node(usuario, tipo="usuario", demanda=demanda, pos=(0, 0))
    for usuario, servidor, latencia in aristas:
        G.add_edge(usuario, servidor, weight=latencia)

    return G, list(capacidades.keys()), list(demandas.keys())


def test_elige_el_servidor_de_menor_latencia_si_ambos_tienen_hueco():
    G, servidores, usuarios = _construir_red_manual(
        aristas=[("Usuario_0", "Servidor_A", 10), ("Usuario_0", "Servidor_B", 5)],
        capacidades={"Servidor_A": 5, "Servidor_B": 5},
        demandas={"Usuario_0": 1},
    )

    asignaciones, _latencia_total = solver_voraz(G, servidores, usuarios)

    assert asignaciones["Usuario_0"] == ("Servidor_B", 5)


def test_si_el_servidor_mas_cercano_esta_lleno_prueba_el_siguiente():
    G, servidores, usuarios = _construir_red_manual(
        aristas=[
            ("Usuario_0", "Servidor_A", 5), ("Usuario_0", "Servidor_B", 20),
            ("Usuario_1", "Servidor_A", 5), ("Usuario_1", "Servidor_B", 20),
        ],
        capacidades={"Servidor_A": 1, "Servidor_B": 5},
        demandas={"Usuario_0": 1, "Usuario_1": 1},
    )

    asignaciones, _latencia_total = solver_voraz(G, servidores, usuarios)

    # Servidor_A solo tiene hueco para uno: al segundo usuario le toca el
    # más lejano en vez de quedarse sin asignar.
    assert asignaciones["Usuario_0"] == ("Servidor_A", 5)
    assert asignaciones["Usuario_1"] == ("Servidor_B", 20)


def test_el_orden_de_los_usuarios_condiciona_el_resultado():
    # Limitación real del algoritmo voraz (y diferencia frente al exacto):
    # como procesa usuarios uno a uno sin volver atrás, quien aparece
    # primero en lista_usuarios se queda con el único hueco disponible.
    G, servidores, _usuarios = _construir_red_manual(
        aristas=[("Usuario_0", "Servidor_A", 5), ("Usuario_1", "Servidor_A", 5)],
        capacidades={"Servidor_A": 1},
        demandas={"Usuario_0": 1, "Usuario_1": 1},
    )

    asignaciones_1, _latencia_total_1 = solver_voraz(G, servidores, ["Usuario_0", "Usuario_1"])
    assert "Usuario_0" in asignaciones_1
    assert "Usuario_1" not in asignaciones_1

    asignaciones_2, _latencia_total_2 = solver_voraz(G, servidores, ["Usuario_1", "Usuario_0"])
    assert "Usuario_1" in asignaciones_2
    assert "Usuario_0" not in asignaciones_2
