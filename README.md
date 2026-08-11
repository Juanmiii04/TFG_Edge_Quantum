# Simulación de balanceo de Cargas Edge computing con computación cuántica

Este repositorio contiene el código de mi TFG. Estoy investigando y simulando cómo repartir de forma eficiente la carga de trabajo en entornos de Edge Computing (balanceo de cargas), comparando algoritmos clásicos de toda la vida con enfoques de computación cuántica. El objetivo principal es utilizar esta base clásica para formular el problema matemáticamente (QUBO) y evaluar la viabilidad de los algoritmos de computación cuántica en la resolución eficiente de cuellos de botella en la red.

# ¿Qué hay en cada carpeta?

Para tener el proyecto bien ordenado, he dividido el código de esta forma:

*   `main_experimentos.ipynb`: Es el cuaderno principal de Jupyter. Desde aquí controlo y ejecuto todas las simulaciones y experimentos.

*   `src/`
    *   `generador_red.py`: Genera la red de simulación (coloca los servidores Edge, los usuarios, y calcula las latencias y demandas de recursos).
    *   `solver_voraz.py`: Resuelve el balanceo usando un algoritmo clásico voraz (greedy).
    *   `solver_exacto.py`: Encuentra la solución óptima exacta con programación lineal entera (PuLP).
    *   `solver_cuantico.py`: Resuelve el mismo problema con computación cuántica (QUBO + QAOA, con Qiskit). Puede ejecutarse tanto en simulador local como en un ordenador cuántico real de IBM.
    *   `gestor_redes.py`: Guarda y recarga redes generadas en JSON, para poder repetir experimentos sobre la misma red exacta.
    *   `visualizador.py`: Dibuja la red y las asignaciones de cada solver sobre un mapa.
    *   `benchmark.py` y `_benchmark_worker.py`: Miden cómo escalan los tres algoritmos (tiempo de ejecución y calidad de la solución) al crecer el tamaño de la red. Cada ejecución se lanza en un proceso aparte con un límite de tiempo, para que un solver que se atasque no cuelgue todo el experimento, y se paralelizan varias ejecuciones a la vez para ir más rápido.

*   `data/`: Redes generadas guardadas (para poder repetir un experimento concreto sin depender del azar) y los resultados de los benchmarks: tablas en CSV y las gráficas ya generadas, listas para meter en la memoria.

# Cómo usar el código

El proyecto usa un entorno virtual (`.venv`) para no tener problemas con las versiones de las librerías. Para instalar todo lo necesario, ejecuta en tu terminal:

> pip install -r requirements.txt

Y desde ahí, todo se controla abriendo y ejecutando `main_experimentos.ipynb`.

# Dónde estoy ahora mismo

La comparación de los tres algoritmos ya funciona de principio a fin (red → tres solvers → resultados → gráficas), y he montyado un experimento para ver cómo escala cada uno al crecer la red (de pocos usuarios hasta cientos).

Al hacerlo me he encotado con algo que no esperaba: si dejo que cada usuario alcance muchos servidores a la vez (red muy conectada), el algoritmo exacto se dispara en tiempo según crece la red (el resultado clásico que estaba buscando) pero el voraz al tener muchos servidores a su alcance el resultado no es tan amlo como esperaba. Pero si limito la conexión a un radio de cobertura realista (que cada usuario solo vea a los servidores físicamente cercanos), el algoritmo exacto aguanta bien(no se topa con un muro que daría sentido al uso de un algoritmo cuántico en el momento que la tecnología lo permita) incluso con redes grandes. 

Es decir, el resultado depende mucho de qué tan "densa" es la red que simulo, y ahora mismo tengo dos formas de resolverlo sobre la mesa:

1. Presentar dos escenarios por separado (uno de red dispersa, tipo zona rural con pocas antenas cerca, y otro de red densa, tipo despliegue urbano con muchas antenas solapadas), cada uno con su propia conclusión.
2. Buscar una configuración de red intermedia que combine ambos efectos en un único experimento más representativo.

Todavía no lo he decidido del todo, es lo próximo que tengo que cerrar antes de poder escribir esta parte de la memoria con seguridad.

# Qué me queda por hacer

Lo siguiente es probar el solver cuántico en un ordenador cuántico real de IBM, en vez de solo en el simulador local. Como el hardware real tiene muchos más qubits disponibles que lo que puedo simular en mi portátil, voy a poder probarlo con redes bastante más grandes de lo que he podido hasta ahora. También quiero aprovechar para medir cuánto empeora la solución por el ruido que tienen los procesadores cuánticos actuales, comparando el resultado ideal (simulado) contra el resultado real (con ruido de hardware).
