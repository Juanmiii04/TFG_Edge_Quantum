import networkx as nx
import random 
import math

#GENERADOR DE RED
def generar_red(num_serv, num_usr, capacidad_max, radio_cobertura=50):
    
    G = nx.Graph()
    list_serv =  []
    list_usr =  []

    # Servidores (con capacidad y posición x,y)
    for i in range(num_serv):
        nombre_servidor = f"Servidor_{i}"
        coord_x = random.randint(0, 100)
        coord_y = random.randint(0, 100)
        G.add_node(nombre_servidor, tipo="servidor", capacidad=capacidad_max, pos=(coord_x, coord_y))
        list_serv.append(nombre_servidor)

    # Usuarios (demanda de recursos y posición x,y)
    for i in range(num_usr):
        nombre_usuario = f"Usuario_{i}"
        coord_x = random.randint(0, 100)
        coord_y = random.randint(0, 100)
        
        #Asignamos una demanda aleatoria
        demanda_recursos = random.randint(1, 3) 
        
        G.add_node(nombre_usuario, tipo="usuario", pos=(coord_x, coord_y), demanda=demanda_recursos)
        list_usr.append(nombre_usuario)

    # Creamos cables con sus latencias
    for usuario in list_usr:
        pos_u = G.nodes[usuario]['pos']
        
        # Guardaremos las distancias para encontrar el más cercano
        distancias_servidores = []
        
        for servidor in list_serv:
            pos_s = G.nodes[servidor]['pos']
            distancia_km = math.dist(pos_u, pos_s)
            distancias_servidores.append((servidor, distancia_km))
            
        # Ordenamos para saber cuál es el más cercano
        distancias_servidores.sort(key=lambda x: x[1])
        
        # Conectamos con los servidores a su alcance
        for i, (servidor, distancia_km) in enumerate(distancias_servidores):
            # Se conecta si está dentro del radio de cobertura
            if distancia_km <= radio_cobertura or i == 0: #si no tiene ningun servidor a su alcance por lo menos se conecta con el más cercano
                
                #le damos un poco de 'realismo' para sacar las latencias
                latencia_base = 5.0 
                saltos_router = distancia_km // 10 #suponemos que hay un router/switch cada 10km
                retardo_saltos = saltos_router * 4.0 #tiempo en ese router
                ruido_red = random.uniform(-2.0, 5.0)
                latencia_total = int(latencia_base + retardo_saltos + ruido_red) #sacamos la latencia total
                
                G.add_edge(usuario, servidor, weight=latencia_total)
    
    return G, list_serv, list_usr
