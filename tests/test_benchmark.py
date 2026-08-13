import pytest

from src.benchmark import LIMITE_QUBITS, ejecutar_benchmark_escalabilidad


@pytest.mark.slow
def test_ejecutar_benchmark_escalabilidad_devuelve_una_fila_por_solver():
    """
    Red mínima (1 servidor, 3 usuarios): todos los usuarios acaban conectados al
    único servidor disponible (fallback del más cercano), así que el número de
    qubits base (6) se queda muy por debajo de LIMITE_QUBITS y el cuántico también
    entra en el benchmark -- por eso este test es lento de verdad (intenta QAOA
    igual que test_solver_cuantico.py). No comprobamos que el cuántico complete a
    tiempo (con un timeout tan ajustado como el por defecto puede o no lograrlo, y
    eso no es lo que este test quiere comprobar), solo que aparece como fila con
    el resto de columnas del DataFrame.
    """
    resultado = ejecutar_benchmark_escalabilidad(
        tamanios_usuarios=[3], num_servidores=1, capacidad_max=5, radio_cobertura=100,
        repeticiones=1,
    )

    columnas_esperadas = {
        "tamanio", "num_servidores", "solver", "tiempo_medio_s",
        "latencia_media", "usuarios_sin_asignar_media", "num_qubits_estimado",
    }
    assert columnas_esperadas.issubset(resultado.columns)

    assert len(resultado) == 3
    assert set(resultado["solver"]) == {"voraz", "exacto", "cuantico"}
    assert (resultado["num_qubits_estimado"] < LIMITE_QUBITS).all()

    # Voraz y exacto son deterministas y casi instantáneos: esos sí deben completar.
    filas_clasicas = resultado[resultado["solver"] != "cuantico"]
    assert filas_clasicas["tiempo_medio_s"].notna().all()


def test_timeout_muy_bajo_deja_nan_en_vez_de_fallar():
    # Con un timeout de 0.01s ningún solver puede llegar a completarse a tiempo --
    # ni siquiera el voraz, que además de su propio cálculo (instantáneo) tiene que
    # levantar un intérprete de Python nuevo como subproceso aislado. Comprobamos
    # que eso se traduce en NaN para esa fila, no en una excepción propagada ni en
    # que ejecutar_benchmark_escalabilidad se quede colgado.
    resultado = ejecutar_benchmark_escalabilidad(
        tamanios_usuarios=[3], num_servidores=1, capacidad_max=5, radio_cobertura=100,
        repeticiones=1, timeout_s=0.01,
    )

    assert not resultado.empty
    assert resultado["tiempo_medio_s"].isna().all()
    assert resultado["latencia_media"].isna().all()
    assert resultado["usuarios_sin_asignar_media"].isna().all()
