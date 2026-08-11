import json
import networkx as nx
import os

def guardar_red(G, servidores, usuarios, filepath="data/red_interesante.json"):
    """
    Guarda el grafo completo (G), y las listas de servidores y usuarios en un archivo JSON.
    """
    # Asegurar que la carpeta data/ existe
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    
    # Extraer los datos del grafo de NetworkX a un formato básico de Python
    data_grafo = nx.node_link_data(G)
    
    # Crear un paquete con toda la información
    paquete = {
        "servidores": servidores,
        "usuarios": usuarios,
        "grafo": data_grafo
    }
    
    # Escribir a JSON
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(paquete, f, indent=4)
        
    print(f"✅ Red guardada exitosamente en: {filepath}")

def cargar_red(filepath="data/red_interesante.json"):
    """
    Carga el grafo (G), servidores y usuarios desde un archivo JSON.
    """
    if not os.path.exists(filepath):
        print(f"❌ Error: El archivo {filepath} no existe.")
        return None, None, None
        
    with open(filepath, 'r', encoding='utf-8') as f:
        paquete = json.load(f)
        
    # Reconstruir listas y el grafo
    servidores = paquete["servidores"]
    usuarios = paquete["usuarios"]
    
    # Reconstruir G
    G = nx.node_link_graph(paquete["grafo"])
    
    print(f"✅ Red cargada exitosamente desde: {filepath}")
    print(f"   -> {len(servidores)} Servidores y {len(usuarios)} Usuarios recuperados.")
    
    return G, servidores, usuarios
