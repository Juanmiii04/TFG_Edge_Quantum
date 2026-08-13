"""
Constantes compartidas entre los tres solvers (y sus tests).

PENALIZACION estaba antes duplicada como una variable local en solver_voraz.py,
solver_exacto.py y solver_cuantico.py -- una decisión consciente en su momento para
que cada solver se pudiera leer/copiar de forma completamente independiente. El
problema es que los tests necesitan conocer ese mismo valor para comprobar que la
penalización se aplica bien (ver test_contrato_solvers.py, test_solver_exacto.py),
así que la duplicación se había extendido también a los tests, con comentarios que
remitían a un CLAUDE.md para la justificación -- un archivo que existe en local pero
está deliberadamente excluido del repositorio (ver .gitignore), así que esa
referencia no lleva a ningún sitio para quien clona el proyecto. Centralizar aquí
evita tanto la referencia muerta como el riesgo de que el valor diverja entre los
solvers y los tests que lo comprueban.
"""

PENALIZACION = 1000  # ms de penalización por cada usuario que se queda sin asignar
