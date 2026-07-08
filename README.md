# Simulación de balanceo de Cargas Edge computing con computación cuántica

Este repositorio contiene el código de mi TFG. Estoy investigando y simulando cómo repartir de forma eficiente la carga de trabajo en entornos de Edge Computing (balanceo de cargas), comparando algoritmos clásicos de toda la vida con enfoques de computación cuántica. El objetivo principal es utilizar esta base clásica para formular el problema matemáticamente (QUBO) y evaluar la viabilidad de los algoritmos de computación cuántica en la resolución eficiente de cuellos de botella en la red.

# ¿Qué hay en cada carpeta? 

Para tener el proyecto bien ordenado, he dividido el código de esta forma:

*   `main_experimentos.ipynb`: Es el cuaderno principal de Jupyter. Desde aquí          controlo   y ejecuto todas las simulaciones y experimentos.

*   `src/`
          `generador_red.py`: Genera nuestra red de simulación (coloca los servidores Edge, los usuarios, y calcula las latencias y demandas de recursos).
          `solver_voraz.py`: Resuelve el balanceo usando un algoritmo clásico voraz (greedy).
          `solver_exacto.py`: Encontrará la solución óptima exacta mediante métodos clásicos.
        `solver_cuantico.py`:Resolverá el problema usando computación cuántica.

*   `data/`: La carpeta donde se guardan las redes generadas y los resultados de las    simulaciones.

# Cómo usar el código 

El proyecto usa un entorno virtual (`.venv`) para no tener problemas con las versiones de las librerías. Para instalar todo lo necesario, ejecuta en tu terminal:


> pip install -r requirements.txt

