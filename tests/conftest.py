import pytest

from src.generador_red import generar_red


@pytest.fixture
def red_pequena_ok():
    """
    Red pequeña y determinista (seed fija) donde todos los usuarios caben.

    Usamos una capacidad por servidor (9) igual a la demanda máxima posible
    de los 3 usuarios (3 usuarios x demanda máxima 3 = 9), así que un único
    servidor ya podría acoger a todos sin importar qué demandas les toquen
    en el sorteo. El radio de cobertura es más grande que la diagonal del
    área (100x100 -> diagonal ~141), así que no hay problemas de alcance.
    """
    return generar_red(
        num_serv=2,
        num_usr=3,
        capacidad_max=9,
        radio_cobertura=200,
        seed=42,
        lado_area=100,
    )


@pytest.fixture
def red_pequena_sobrecargada():
    """
    Red pequeña deliberadamente sobrecargada: la capacidad total de la red
    (2 servidores x 1 de capacidad = 2) es muchísimo menor que la demanda
    mínima posible de los 6 usuarios (6 x demanda mínima 1 = 6), así que
    siempre se quedan usuarios sin asignar, sea cual sea el sorteo de
    demandas. El radio de cobertura es amplio para que el motivo de que se
    queden usuarios fuera sea la capacidad y no el alcance de la red.
    """
    return generar_red(
        num_serv=2,
        num_usr=6,
        capacidad_max=1,
        radio_cobertura=200,
        seed=42,
        lado_area=100,
    )
