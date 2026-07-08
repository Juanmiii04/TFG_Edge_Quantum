import pulp

def solver_exacto(G, lista_servidores, lista_usuarios):
    print("Iniciamos algoritmo exacto (PuLP):")
    
    PENALIZACION = 1000
    
    #Creamos el problema (minimización)
    prob = pulp.LpProblem("Balanceo_Edge", pulp.LpMinimize)
    
    #Creamos las variables de decisión
    # x[u, s] vale 1 si el usuario u se asigna al servidor s
    x = pulp.LpVariable.dicts("asignacion", ((u, s) for u in lista_usuarios for s in G[u]),cat='Binary')
                              
    # y[u] vale 1 si el usuario u se queda sin asignar
    y = pulp.LpVariable.dicts("desconectado", lista_usuarios, cat='Binary')
                              
    #Creamos la función objetivo(consiste en minimizar la latencia teniendo en cuenta los usuarios no asignados)
    latencias_asignaciones = pulp.lpSum(x[u, s] * G[u][s]['weight'] for u in lista_usuarios for s in G[u])
    latencias_penalizaciones = pulp.lpSum(y[u] * PENALIZACION for u in lista_usuarios)
    prob += latencias_asignaciones + latencias_penalizaciones, "Latencia_Total"
    
    #Creamos las restricciones 
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
        
    #Imprimimos los  resultados igual que el algoritmo voraz
    for servidor in lista_servidores:
        usuarios_este_servidor = [
            f"{u} ({asignaciones[u][1]}ms, dem: {G.nodes[u].get('demanda', 1)})" 
            for u in asignaciones if asignaciones[u][0] == servidor
        ]
        print(f" {servidor} (Ocupación recursos: {ocupacion_servidores[servidor]}/{G.nodes[servidor]['capacidad']}): {', '.join(usuarios_este_servidor)}")
        
    print(f"\n Latencia total de la red (Exacto): {latencia_total} ms")
    if usuarios_sin_asignar:
        print(f" -> Detalle: {latencia_asignada} ms (Asignados) + {latencia_penalizacion} ms (Penalización por {len(usuarios_sin_asignar)} desconectados)")
        print(f" Usuarios desconectados: {', '.join(usuarios_sin_asignar)}")
   
    
    return asignaciones, latencia_total
