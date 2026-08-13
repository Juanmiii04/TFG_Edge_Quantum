from src.constantes import PENALIZACION


def solver_voraz(G, lista_servidores, lista_usuarios):
    print("Iniciamos algoritmo voraz:")

    #Prepararamos los  contadores
    ocupacion_servidores = {s: 0 for s in lista_servidores}#con un diccionario llevamos la ocupación de cada servidor
    asignaciones = {} # Guardamos el usuario y la latencia en el servidor que hemos asignado
    latencia_asignada = 0
    usuarios_sin_asignar = []

    #Buscamos el sitio para cada usuario
    for usuario in lista_usuarios:
        # Obtenemos la demanda del usuario 
        demanda_usr = G.nodes[usuario].get('demanda', 1) #si por lo que sea no tiene asignada una demanda, le asignamos por defecto 1
        
        # Ordenamos las latencias de menor a mayor
        conexiones = G[usuario]
        servidores_ordenados = sorted(conexiones.items(), key=lambda x: x[1]['weight'])
        
        asignado = False
        
        # Comprobamos servidores empezando por el más cercano
        for servidor, datos_cable in servidores_ordenados:
            latencia = datos_cable['weight']
            capacidad_max = G.nodes[servidor]['capacidad']
            
            #Miramos si hay hueco para la demanda completa del usuario
            if ocupacion_servidores[servidor] + demanda_usr <= capacidad_max:
                # Si se puede asignar actualizamos la ocupación con la demanda del usuario
                ocupacion_servidores[servidor] += demanda_usr
                asignaciones[usuario] = (servidor, latencia)
                latencia_asignada += latencia
                asignado = True
                break # Una vez asignado pasamos al siguiente usuario
        
        # Si después de mirar todos los servidores no cabe, lo anotamos
        if not asignado:
            usuarios_sin_asignar.append(usuario)

    #Cálculamos la latencia total teniendo en cuenta la penalización de los servidores no asignados
    latencia_penalizacion = len(usuarios_sin_asignar) * PENALIZACION
    latencia_total = latencia_asignada + latencia_penalizacion

    # Mostramos resultado
    for servidor in lista_servidores:
        usuarios_este_servidor = []
    
        for u, (servidor_asignado, latencia) in asignaciones.items():
            if servidor_asignado == servidor:
                demanda = G.nodes[u].get('demanda', 1)
                usuarios_este_servidor.append(f"{u} ({latencia}ms, dem: {demanda})")
    
        ocupacion = ocupacion_servidores[servidor]
        capacidad = G.nodes[servidor]['capacidad']
    
        texto_usuarios = ', '.join(usuarios_este_servidor)
        print(f" {servidor} (Ocupación recursos: {ocupacion}/{capacidad}): {texto_usuarios}")

    print(f"\n Latencia total de la red (Voraz): {latencia_total} ms")

    if usuarios_sin_asignar:
        num_desc = len(usuarios_sin_asignar)
        texto_desc = ', '.join(usuarios_sin_asignar)

        print(f" -> Latencia total detallada: {latencia_asignada} ms (Asignados) + {latencia_penalizacion} ms (Penalización por {num_desc} desconectados)")
        print(f" Usuarios desconectados: {texto_desc}")

    return asignaciones, latencia_total
