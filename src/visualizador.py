import matplotlib.pyplot as plt
import networkx as nx

def dibujar_asignaciones(G, asignaciones, servidores, usuarios, titulo="Asignaciones de Red"):
    """
    Dibuja la topología de la red mostrando visualmente qué usuario se conecta a qué servidor.
    Los usuarios no asignados se resaltan en rojo oscuro.
    """
    plt.figure(figsize=(10, 8))
    pos = nx.get_node_attributes(G, 'pos')
    
    # Separar usuarios asignados de no asignados
    usuarios_asignados = [u for u in usuarios if u in asignaciones]
    usuarios_aislados = [u for u in usuarios if u not in asignaciones]
    
    # 1. Dibujar nodos
    # Servidores (Cuadrados azules)
    nx.draw_networkx_nodes(G, pos, nodelist=servidores, node_color='lightblue', 
                           node_shape='s', node_size=800, label='Servidores')
    
    # Usuarios asignados (Círculos verdes)
    nx.draw_networkx_nodes(G, pos, nodelist=usuarios_asignados, node_color='lightgreen', 
                           node_size=500, label='Usuarios Conectados')
                           
    # Usuarios aislados (Círculos rojos)
    if usuarios_aislados:
        nx.draw_networkx_nodes(G, pos, nodelist=usuarios_aislados, node_color='salmon', 
                               node_size=500, label='Usuarios Aislados')
    
    # 2. Dibujar enlaces de fondo (posibles conexiones, gris punteado)
    nx.draw_networkx_edges(G, pos, edge_color='lightgray', style='dashed', alpha=0.5)
    
    # 3. Dibujar enlaces activos (los seleccionados por el solver)
    enlaces_activos = []
    for u, datos in asignaciones.items():
        s = datos[0] # El servidor asignado (el solver devuelve la tupla (servidor, latencia))
        enlaces_activos.append((u, s))
        
    if enlaces_activos:
        nx.draw_networkx_edges(G, pos, edgelist=enlaces_activos, edge_color='black', width=2.5)
    
    # 4. Etiquetas (Acortar los nombres para que no se solapen)
    etiquetas_cortas = {}
    for nodo in G.nodes():
        if str(nodo).startswith("Usuario_"):
            etiquetas_cortas[nodo] = f"U{str(nodo).split('_')[1]}"
        elif str(nodo).startswith("Servidor_"):
            etiquetas_cortas[nodo] = f"S{str(nodo).split('_')[1]}"
        else:
            etiquetas_cortas[nodo] = str(nodo)
            
    # Dibujar las etiquetas con una fuente más pequeña y un fondo semitransparente para que se lean bien
    nx.draw_networkx_labels(G, pos, labels=etiquetas_cortas, font_size=9, font_weight='bold', 
                            bbox=dict(facecolor='white', edgecolor='none', alpha=0.6, pad=0.5))
    
    plt.title(titulo, fontsize=16, fontweight='bold', pad=20)
    
    # Colocar la leyenda fuera del gráfico para que no tape nodos
    plt.legend(loc='center left', bbox_to_anchor=(1, 0.5), scatterpoints=1, frameon=True, shadow=True)
    
    # Añadir un poco de margen para que los nodos de los bordes no se corten
    plt.margins(0.15)
    plt.axis('off')
    plt.tight_layout()
    plt.show()
