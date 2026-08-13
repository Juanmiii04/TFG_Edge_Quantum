import pulp

from src.constantes import PENALIZACION


def solver_exacto(G, lista_servidores, lista_usuarios):
    print("Iniciamos algoritmo exacto (PuLP):")

    #Creamos el problema a resolver(en este caso minimizar la latencia)
    prob = pulp.LpProblem("Balanceo_Edge", pulp.LpMinimize)
    
    #Creamos las variables de decisión
    # x[u, s] vale 1 si el usuario u se asigna al servidor s
    x = pulp.LpVariable.dicts("asignacion", ((u, s) for u in lista_usuarios for s in G[u]),cat='Binary')
                              
    # y[u] vale 1 si el usuario u se queda sin asignar
    y = pulp.LpVariable.dicts("desconectado", lista_usuarios, cat='Binary')
                              
    #Creamos la función objetivo(consiste en minimizar la latencia teniendo en cuenta la penalización que conlleva los usuarios que no se asignen a ningun servidor)
    latencias_asignaciones = pulp.lpSum(x[u, s] * G[u][s]['weight'] for u in lista_usuarios for s in G[u]) #latencia total de los usuarios que han conseguido conectarse(x[u, s]=1)
    latencias_penalizaciones = pulp.lpSum(y[u] * PENALIZACION for u in lista_usuarios)#latencia total de los usuarios que no se han conectado(x[u, s]=0 y y[u]=1 )
    prob += latencias_asignaciones + latencias_penalizaciones, "Latencia_Total" #prueba todas las combinaciones de los sumatorios anteriores hasta dar con el de menor latencia
    
    #Creamos las restricciones físicas(no todas las combinaciones están permitidas)
    #Restricción 1: Cada usuario se conecta a un único servidor, o se queda desconectado (y=1)
    for u in lista_usuarios:
        prob += pulp.lpSum(x[u, s] for s in G[u]) + y[u] == 1, f"Asignacion_Unica_o_Desconexion_{u}"
        
    #Restricción 2: No se puede superar la capacidad de los servidores
    for s in lista_servidores:
        # Suma de las demandas de los usuarios asignados a este servidor
        prob += pulp.lpSum(x[u, s] * G.nodes[u].get('demanda', 1) for u in lista_usuarios if s in G[u]) <= G.nodes[s]['capacidad'], f"Capacidad_{s}"
                           
    #Resolvemos el problema
    prob.solve(pulp.PULP_CBC_CMD(msg=0))#msg=0 para ocultar los logs matemáticos 
    
    #Procesamos resultados
    asignaciones = {}
    latencia_asignada = 0
    ocupacion_servidores = {s: 0 for s in lista_servidores}
    usuarios_sin_asignar = []
    
    if pulp.LpStatus[prob.status] == 'Optimal':
        for u in lista_usuarios:
            if pulp.value(y[u]) == 1:
                usuarios_sin_asignar.append(u) #usuarios sin asignar
            else:
                for s in G[u]:
                    if pulp.value(x[u, s]) == 1: #añadimos los datos de los usuarios asignados
                        latencia = G[u][s]['weight']
                        demanda = G.nodes[u].get('demanda', 1)
                        
                        asignaciones[u] = (s, latencia)
                        latencia_asignada += latencia
                        ocupacion_servidores[s] += demanda
    else:
        print("Error matemático: No se encontró solución.")
        return {}, 0
        
    latencia_penalizacion = len(usuarios_sin_asignar) * PENALIZACION
    latencia_total = latencia_asignada + latencia_penalizacion
        
    #imprimimos los resultados 
    for servidor in lista_servidores:
        usuarios_este_servidor = []
        
        # Desempaquetamos el diccionario de asignaciones 
        for u, (servidor_asignado, latencia) in asignaciones.items():
            if servidor_asignado == servidor:
                demanda = G.nodes[u].get('demanda', 1)
                usuarios_este_servidor.append(f"{u} ({latencia}ms, dem: {demanda})")
                
        # Extraemos los datos del servidor a variables limpias
        ocupacion = ocupacion_servidores[servidor]
        capacidad = G.nodes[servidor]['capacidad']
        texto_usuarios = ', '.join(usuarios_este_servidor)
        
        print(f" {servidor} (Ocupación recursos: {ocupacion}/{capacidad}): {texto_usuarios}")
        
    print(f"\n Latencia total de la red (Exacto): {latencia_total} ms")
    
    if usuarios_sin_asignar:
        num_desc = len(usuarios_sin_asignar)
        texto_desc = ', '.join(usuarios_sin_asignar)
        
        print(f" -> Latencia total detallada: {latencia_asignada} ms (Asignados) + {latencia_penalizacion} ms (Penalización por {num_desc} desconectados)")
        print(f" Usuarios desconectados: {texto_desc}")
   
    return asignaciones, latencia_total
