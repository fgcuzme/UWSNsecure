from tangle2_light import create_gen_block, create_transaction, sign_transaction, verify_transaction_signature
from bbdd2_sqlite3 import load_keys_shared_withou_cipher, load_keys_sign_withou_cipher
from test_throp import propagation_time
import numpy as np
from energia_dinamica import calcular_energia_paquete

# import pickle

# # Cargas nodos y sink
# # Para cargar la estructura de nodos guardada
# with open('nodos_guardados.pkl', 'rb') as file:
#     node_uw = pickle.load(file)

# # Para cargar la estructura de nodos guardada
# with open('sink_guardado.pkl', 'rb') as file:
#     nodo_sink = pickle.load(file)

# # print(nodo_sink)

import random
import time

# Consideramos un escenario ideal donde todas las Tx llegan a su destino
# success_rate = 0
def propagate_with_probability(success_rate = 0):
    """
    Simula la probabilidad de éxito de la propagación de una transacción.
    Parameters:
    success_rate: Probabilidad de éxito en la propagación de la transacción (por defecto 80%).
    Returns:
    True si la propagación es exitosa (según el valor aleatorio y la tasa de éxito), False en caso contrario.
    """
    return random.random() > success_rate


stats = {
    "energy": {
        "CH": {
            "tx": [],    # Energía en transmisión
            "rx": []     # Energía en recepción
        },
        "SN": {
            "tx": [],
            "rx": []
        }
    },

    "times": {
        "propagation": [],    # Tiempos de propagación
        "propagation_all": [],# Tiempos de propagación total
        "verification": [],   # Tiempos de verificación
        "response": []        # Tiempos de respuesta
    },
    "attempts": 0            # Reintentos totales
}


# Funcion para propagar tx genesis hacia los CHs
# Los Ch deben validar la tx enviada por el genesis
# Sink -> CH
def propagate_tx_to_ch(sink1, ch_list, node_uw1, genesis_tx, max_retries=3, timeout=2):
    """
    Función para propagar la transacción génesis del Sink a los CHs.
    Si un CH no responde en el tiempo establecido, se reintenta la propagación.
    sink1: Estructura del Sink.
    ch_list: Lista de CHs a los que se propagará la Tx génesis.
    genesis_tx: Transacción génesis creada por el Sink.
    max_retries: Número máximo de reintentos.
    timeout: Tiempo de espera entre reintentos.
    """
    # # Capturar estadisticas nuevas
    # stats = {
    #     "energy_consumed": {"CH": [], "SN": []},
    #     "propagation_times": [],
    #     "verification_times": [],
    #     "propagation_times_all":[]
    # }

    # Listas para almacenar los tiempos de verificación y respuesta por cada CH
    times_verify_all_ch = []
    speed_propagation = []
    # times_response_all_ch = []
    times_propagation_tx = 0

    # Diccionario para capturar estadísticas individuales
    stats_proTx1 = {
        "stats_proTx": {},  # Para guardar estadísticas por cada CH y nodo
    }

    for index_ch in ch_list:
        retries = 0
        #node_ch = node_uw[ch]
        # print('INICIO DE PROPGATE : ', node_ch)

        # Almacena el nodo ch para esta ronda
        Ch_node = node_uw1[index_ch]

        while retries < max_retries:
            # Verificar si el CH está sincronizado, para poder recibir la Tx
            if Ch_node['IsSynced']:
                # print(f"Propagando Tx génesis al CH {node_uw[ch]['NodeID']}")

                time_start_ptx = time.time() # inicia el conteo del tiempo de propagación

                # Aqui toca agregar el delay de propagación basasdo en la formula de distancia/velocidad
                # delay = random_sync_delay()  # Generar un tiempo de retraso aleatorio
                # calcular la distancia entre los nodos
                dist = np.linalg.norm(Ch_node["Position"] - sink1["Position"])
                
                start_position = sink1["Position"]
                end_position = Ch_node["Position"]

                delay = propagation_time(dist, start_position, end_position)
                print(f"Sink enviando Tx genesis (Request_auth) al CH {Ch_node['NodeID']}, retraso de {delay:.2f} segundos, distancia calculada {dist:.2f}")
                time.sleep(delay)  # Simular el tiempo de sincronización
                # speed_propagation.append(speed)
                # print('speed_propagation', speed_propagation)
                times_propagation_tx = times_propagation_tx + (time.time() - time_start_ptx)

                # nueva estadistica
                stats["attempts"] += retries  # Contar reintentos
                
                # Simular probabilidad de recepción
                if propagate_with_probability():

                    # Verificar la Tx con la clave pública del Sink
                    # calcular el tiempo de verificación tx por parte del CH
                    time_start = time.time()
                    isverify = verify_transaction_signature(genesis_tx['ID'], genesis_tx['Signature'], Ch_node['PublicKey_sign_sink'])
                    end_time_verify = time.time() - time_start
                    times_verify_all_ch.append(end_time_verify)  # Guardar el tiempo de verificación para este CH

                    rx_energy = calcular_energia_paquete("tx", es_tx=False)
                    
                    # Calcula el consumo de energía en recepción del CH
                    Ch_node["ResidualEnergy"] -= rx_energy

                    stats_proTx1["stats_proTx"][f"CH_Rx{Ch_node['NodeID']}"] = {
                        "energy_consumed": rx_energy
                        #"sync_time": sync_end_time_node,
                        #"retransmissions": retries,
                        #"is_syn": node["IsSynced"]
                    }
                    
                    # estadisticas nuevas
                    stats["energy"]["CH"]["rx"].append(rx_energy)  # CH recibe
                    stats["times"]["propagation"].append(delay)
                    stats["times"]["verification"].append(end_time_verify)
                    
                    # Verifcar la tx recibida del Sink
                    if isverify:
                        print(f"CH {Ch_node['NodeID']} recibió y verificó la Tx génesis.")
                        
                        Ch_node['Tips'].append(genesis_tx['ID'])    # Se guarda la Tx genesis en el CH

                        # Propagar la Tx Génesis a los nodos del cluster del CH
                        # CH -> SN
                        times_propagation_tx_nodes, node_stats_proTx, stats1 = propagate_genesis_to_cluster(node_uw1, index_ch, genesis_tx, max_retries=3, timeout=2)
                        
                        # capturar estadisticas
                        stats_proTx1["stats_proTx"].update(node_stats_proTx)

                        # suma el tiempo que lleva en cada cluster 
                        times_propagation_tx = times_propagation_tx + times_propagation_tx_nodes
                        
                        # nueva estadistica
                        stats["times"]["propagation_all"].append(times_propagation_tx)

                        recived = True
                        break
                    else:
                        print(f"CH {Ch_node['NodeID']} falló en la verificación de la Tx génesis.")
                        recived = False
                        break
                else:
                    print(f"CH {Ch_node['NodeID']} no recibió la Tx génesis. Reintentando...")
                    retries += 1
                    time.sleep(timeout)
            else:
                print(f"CH {Ch_node['NodeID']} no está sincronizado. Omitido.")
                recived = False
                break

        if retries == max_retries:
            print(f"CH {Ch_node['NodeID']} no respondió tras {max_retries} reintentos.")
            recived = False

    return recived, times_verify_all_ch, times_propagation_tx, stats_proTx1, stats, stats1


# Funcion para propagar la tx genesis hacia cada cluster
# CH -> SN
def propagate_genesis_to_cluster(node_uw2, ch_index, genesis_tx, max_retries=3, timeout=2):
    """
    Propaga la Tx Génesis desde el CH a los nodos sincronizados en su cluster con reintentos.
    node_uw: Diccionario de los nodos.
    ch_index: Índice del CH que está propagando la transacción.
    genesis_tx: Transacción génesis creada por el Sink.
    max_retries: Número máximo de reintentos.
    timeout: Tiempo de espera entre reintentos (en segundos).
    """
    # # Estadisticas
    # stats = {
    #     "tx_energy": [],
    #     "rx_energy":[],
    #     "propagation_delays": []
    # }

    print('Iniciando propagación de la transacción génesis dentro del cluster...')
    indexCH = node_uw2[ch_index]['NodeID']

    # Almacena el nodo CH para esta ronda
    ch_node1 = node_uw2[ch_index]
    #print(indexCH)
    
    # Variable para almacenar el tiempo de propagación de tx genesis
    times_propagation_tx_nodes = 0
    speed_propagation = []

    # Diccionario para capturar estadísticas de cada nodo
    stats_proTx2 = {}
    consumo = 0.0

    # Iterar sobre los nodos del cluster
    for node1 in node_uw2:
        # print(node)
        # Verificar si el nodo pertenece al cluster del CH y está sincronizado
        #print('Nodo for : ', node['NodeID'], 'Nodo estrutura node_uw : ', node_uw[ch_index]['NodeID'])
        if node1['NodeID'] != indexCH and node1['IsSynced'] and node1['ClusterHead'] == indexCH:
            retries = 0
            while retries < max_retries:
                # print(f"Intentando enviar la transacción génesis al nodo {node['NodeID']}... Reintento {retries + 1}/{max_retries}")

                time_start_ptx = time.time() # inicia el conteo del tiempo de propagación

                # Aqui toca agregar el delay de propagación basasdo en la formula de distancia/velocidad
                # delay = random_sync_delay()  # Generar un tiempo de retraso aleatorio
                # calcular la distancia entre los nodos
                dist = np.linalg.norm(ch_node1["Position"] - node1["Position"])
                
                start_position = ch_node1["Position"]
                end_position = node1["Position"]
                delay = propagation_time(dist, start_position, end_position)
                
                print(f"CH {ch_node1['NodeID']} enviando Tx genesis (Request_auth) al nodo {node1['NodeID']}, retraso de {delay:.2f} segundos, distancia calculada {dist:.2f}")
                time.sleep(delay)  # Simular el tiempo de sincronización
                # speed_propagation.append(speed)
                times_propagation_tx_nodes = times_propagation_tx_nodes + (time.time() - time_start_ptx)

                tx_energy = calcular_energia_paquete("tx", es_tx=True)

                # calculo de energia en la Transmision de la TX en el CH -> SN
                ch_node1["ResidualEnergy"] -= tx_energy
                
                consumo += tx_energy

                # Captura estadisticas energia
                stats_proTx2[f"CH_Tx{ch_node1['NodeID']}"] = {
                    "energy_consumed": consumo
                    #"sync_time": sync_end_time_node,
                    #"retransmissions": retries,
                    #"is_syn": node["IsSynced"]
                    }
                             
                # Registrar
                # estadisticas nuevas
                stats["energy"]["CH"]["tx"].append(tx_energy)  # CH trasmite
                stats["times"]["propagation"].append(delay)
                stats["attempts"] += retries  # Contar reintentos
                

                if propagate_with_probability():
                    
                    # Verificar la Tx con la clave pública del Sink
                    # calcular el tiempo de verificación tx por parte del CH
                    time_start = time.time()
                    isverify = verify_transaction_signature(genesis_tx['ID'], genesis_tx['Signature'], node1['PublicKey_sign_sink'])
                    end_time_verify = time.time() - time_start

                    # nueva estadistica
                    stats["times"]["verification"].append(end_time_verify)

                    # Verificar la Tx con la clave pública del Sink
                    if isverify:
                        print(f"Nodo {node1['NodeID']} en cluster {ch_node1['NodeID']} recibió y verificó la Tx génesis.")
                        
                        #id_genesis_tx1 = copy.deepcopy(genesis_tx)
                        node1['Tips'].append(genesis_tx['ID'])   # El nodo agrega la Tx genesis propagada por el CH

                        rx_energy = calcular_energia_paquete("tx", es_tx=False)

                        # Calcula el consumo de energía en recepción de TX del SN - CH -> SN
                        node1["ResidualEnergy"] -= rx_energy

                        # Captura estadisticas energia
                        stats_proTx2[f"Node_Rx{node1['NodeID']}"] = {
                            "energy_consumed": rx_energy
                            #"sync_time": sync_end_time_node,
                            #"retransmissions": retries,
                            #"is_syn": node["IsSynced"]
                        }

                        # Registrar
                        # estadisticas nuevas
                        stats["energy"]["SN"]["rx"].append(rx_energy)  # SN recibe
                        
                        break  # Salir del bucle de reintentos si la verificación es exitosa
                    else:
                        print(f"Nodo {node1['NodeID']} falló en la verificación de la Tx génesis.")
                        retries += 1
                        time.sleep(timeout)
                else:
                    print(f"Nodo {node1['NodeID']} no recibió la Tx génesis. Reintentando... ({retries + 1}/{max_retries})")
                    retries += 1
                    time.sleep(timeout)

            # Si se alcanzan los reintentos máximos
            if retries == max_retries:
                print(f"Nodo {node1['NodeID']} no respondió tras {max_retries} reintentos.")

    return times_propagation_tx_nodes, stats_proTx2, stats

# ####
# # Crear la genesis
# txgenesis = create_gen_block(nodo_sink["NodeID"], nodo_sink["PrivateKey"])

# print(txgenesis)

# pro = propagate_tx_to_ch(nodo_sink, nodo_sink["NeighborCHs"], node_uw, txgenesis, max_retries=3, timeout=2)

# print(pro)

def select_tips(tips, num_tips):
    """
    Selecciona un número determinado de tips al azar.
    Args:
        tips (list): Lista de tips disponibles.
        num_tips (int): Número de tips que se desea seleccionar.
    Returns:
        list: Lista con los tips seleccionados.
    """
    if len(tips) >= num_tips:
        selected_tips = random.sample(tips, num_tips)  # Selecciona tips al azar sin repetición
    else:
        selected_tips = tips  # Si hay menos tips, selecciona todos los disponibles
    return selected_tips


def find_tip_index(tips, tip_id):
    """
    Encuentra el índice de un tip en la lista basado en su ID.
    Args:
        tips (list): Lista de tips, donde cada tip es un diccionario con un campo 'ID'.
        tip_id (str): El ID del tip que estamos buscando.
    Returns:
        int: El índice del tip si se encuentra, o -1 si no se encuentra.
    """
    for index, tip in enumerate(tips):
        if tip["ID"] == tip_id:
            return index  # Retorna el índice tan pronto como lo encuentra
    return -1  # Si no encuentra el tip, retorna -1


def create_auth_response_tx(node_ch1):
    """
    Crea una nueva transacción de respuesta de autenticación para el Sink.
    """
    # Seleccionar dos tips a aprobar (si están disponibles)
    tips_tx = node_ch1['Tips']
    approved_tips1 = select_tips(tips_tx, 2)

    print('approved_tips Toma dos tips para generar la Tx de respuesta :', approved_tips1, ' -> ID : ', node_ch1['NodeID'])

    # Crear el payload para la transacción de autenticación
    payload = f'{node_ch1["NodeID"]};{node_ch1["Id_pair_keys_sign"]};{node_ch1["Id_pair_keys_shared"]}'

    # Crear una nueva transacción de autenticación aprobando los tips
    new_tx = create_transaction(node_ch1['NodeID'], payload, '1', approved_tips1, node_ch1['PrivateKey_sign'])

    # Agrega la nueva transacción y agregarla a los tips del CH
    node_ch1['Transactions'].append(new_tx)
    # node_ch1['Tips'].append(new_tx['ID'])

    return new_tx


from bbdd2_sqlite3 import load_keys_shared_withou_cipher, load_keys_sign_withou_cipher
from copy import deepcopy

# Funcion para propagar respuesta de los ch al sink
# CH -> Sink
# CH -> SN
def propagate_tx_to_sink_and_cluster(sink1, list_ch, node_uw3, max_retries=3, timeout=2):
    """
    Propaga la Tx de respuesta de autenticación desde el CH al Sink y a los nodos de su cluster con reintentos.
    node_ch2: Nodo CH que está propagando la transacción.
    sink: Nodo Sink que recibirá la Tx.
    node_uw: Diccionario de los nodos.
    auth_response_tx: Transacción de respuesta de autenticación creada por el CH.
    max_retries: Número máximo de reintentos.
    timeout: Tiempo de espera entre reintentos (en segundos).
    """

    # # Estadisticas
    # stats = {
    #     "energy_breakdown": {
    #         "CH_tx": [],
    #         #"CH_rx": [],
    #         "SN_rx": []
    #     },
    #     "attempts": 0
    # }

    #Id_nodeCH = node_ch2['NodeID']

    #print('Nodo que se va actualizar el auth en el sink: ', Id_nodeCH)

    # Listas para almacenar los tiempos de verificación y respuesta por cada CH
    times_verify_all_ch = []
    times_response_all_ch = []

    # Variable para almacenar el tiempo de propagación de tx respuesta del CH
    # al sink y nodos del cluster
    times_propagation_tx_response = 0
    
    # Diccionario para capturar estadísticas individuales
    stats_proTx2 = {
        "stats_proTx": {},  # Para guardar estadísticas por cada CH y nodo
    }
    
    consumo1 = 0.0 

    for ch_index in list_ch:
        print('Iniciando propagación de la transacción respuesta del CH al sink y dentro del cluster...')
        indexCH = node_uw3[ch_index]['NodeID']

        # Almacena el nodo CH para esta ronda
        ch_node1 = node_uw3[ch_index]

        # Crear la nueva transacción de respuesta y propagarla al Sink
        # Response_auth_to_sink
        time_start_responseCH = time.time() # Incia tiempo de medición de la creación de la nueva Tx de response
        auth_response_tx1 = create_auth_response_tx(ch_node1)
        print('#####')
        print('Transacción de auth creada por el ch : ', auth_response_tx1)
        print('####')
        end_time_responseCH = time.time() - time_start_responseCH
        times_response_all_ch.append(end_time_responseCH)  # Guardar el tiempo de respuesta para este CH

        # Crear una copia profunda de la transacción para evitar referencias compartidas
        auth_response_tx_sink = deepcopy(auth_response_tx1)
        auth_response_tx_ch = deepcopy(auth_response_tx1)

        # # Actualizar la tx de Tips a ApprovedTransactions del ch
        update_transactions(ch_node1, auth_response_tx_ch)  # corregido

        # 
        # Eliminar la tx que genera conflicto, para solucionar la eliminación de tx aprobada
        id_transaction = auth_response_tx_ch['ID']
        # Eliminar la transacción
        delete_transaction(ch_node1, id_transaction) # corregido

        # # Aqui se agrega la TX en el tips del nodo
        ch_node1['Tips'].append(id_transaction)     # corregido
        
        # Se vuelve agregar la tx en el nodo
        ch_node1['Transactions'].append(auth_response_tx_ch)    # corregido

        retries = 0
        while retries < max_retries:
            
            start_response_tx_ch = time.time()
            # Se puede medir el tiempo de propagación de la Tx dentro del cluster
            # Aqui toca agregar el delay de propagación basasdo en la formula de distancia/velocidad
            # delay = random_sync_delay()  # Generar un tiempo de retraso aleatorio
            # calcular la distancia entre los nodos
            dist = np.linalg.norm(ch_node1["Position"] - sink1["Position"])
            
            start_position = ch_node1["Position"]
            end_position = sink1["Position"]
            delay = propagation_time(dist, start_position, end_position)
            
            print(f"CH {ch_node1['NodeID']} enviando Tx Response_auth_to_sink, retraso de {delay:.2f} segundos, distancia calculada {dist:.2f}")
            time.sleep(delay)  # Simular el tiempo de sincronización

            times_propagation_tx_response = times_propagation_tx_response + (time.time() - start_response_tx_ch)

            tx_energy = calcular_energia_paquete("tx", es_tx=True)

            # calculo de energia en la Transmision de la TX_response del CH -> Sink
            ch_node1["ResidualEnergy"] -= tx_energy

            # Medición por cada transmisión CH→Sink
            # estadisticas nuevas
            stats["energy"]["CH"]["tx"].append(tx_energy)  # CH trasmite
            stats["times"]["propagation"].append(delay)
            stats["attempts"] += retries  # Contar reintentos

            # Captura estadisticas energia
            stats_proTx2["stats_proTx"][f"CH_Tx{ch_node1['NodeID']}"] = {
                "energy_consumed": tx_energy
                #"sync_time": sync_end_time_node,
                #"retransmissions": retries,
                #"is_syn": node["IsSynced"]
            }
            
            print('####')
            print('Antes de actualizar el CH imprimimos el esatdo del nodo : ', ch_node1)
            print('####')

            # # Aqui se agrega la TX en el tips del nodo
            # ch_node1['Tips'].append(auth_response_tx1['ID'])

            # # Tambien se debe actualizar el propio nodo con la Tx que esta aprobando
            # update_transactions(ch_node1, auth_response_tx1)

            print('####')
            print('Despues de actualizar el CH imprimimos el esatdo del nodo : ', ch_node1)
            print('####')

            # Simular la probabiidad de recepción
            if propagate_with_probability():

                # El CH coloca su estado de autenticado cuando inicia el proceso de propagación de la TX
                ch_node1['Authenticated'] = True

                # print(f"El sink recibio la Tx del CH {ch['NodeID']}")

                payload = auth_response_tx1['Payload']
                # Dividir el payload por el separador ";"
                payload_parts = payload.split(';') # obtener el identificador de la firma utilizada
                id_pair_keys_sign = payload_parts[1] # Obtener el identificador del par de firmas (segundo elemento)

                # Si la tx llega al nodo debe identificar la id de la clave utilizada para validar la firma
                _, key_public_sign = load_keys_sign_withou_cipher("bbdd_keys_shared_sign_cipher.db", "keys_sign_ed25519",
                                                                index=id_pair_keys_sign)

                # La tx es verificada por el sink con la firma publica obtenida de la bbdd, el identificador 
                # de la firma se envio en el payload
                if verify_transaction_signature(auth_response_tx1['ID'], auth_response_tx1['Signature'], key_public_sign):

                    print(f"El Sink recibió y verificó la Tx de Response_auth_to_sink de CH {ch_node1['NodeID']}")
                    sink1['Tips'].append(auth_response_tx1['ID'])

                    # Cuando hace la verificación de la Tx el sink puede indicar que el CH esta autenticado, en su registro
                    # Le restamos uno al Id_nodeCH porque accede por lista en ese orden.
                    sink1['RegisterNodes'][indexCH - 1]['Status_auth'] = True

                    print(f"Se actualizo información del nodo {ch_node1['NodeID']},  en el Sink {sink1['RegisterNodes'][indexCH - 1]['Status_auth']}")

                    # Actualizar las transacciones en el sink
                    update_transactions(sink1, auth_response_tx_sink)

                    print('Verificamos que el sink ha actualizado las tx de forma correcta : ', sink1)

                    break
                else:
                    print(f"El Sink falló en la verificación de la Tx de CH {ch_node1['NodeID']}")
                    retries += 1
                    time.sleep(timeout)

        if retries == max_retries:
            print(f"Sink {sink1['NodeID']} no respondió tras {max_retries} reintentos.")


        # # Aqui se agrega la TX en el tips del nodo
        # ch_node1['Tips'].append(auth_response_tx1['ID'])

        # # Actualizar la tx de Tips a ApprovedTransactions del ch
        # update_transactions(ch_node1, auth_response_tx1)

        ##
        ##
        # Propagar la respuesta del CH a los nodos del cluster
        # CH -> SN
        for node2 in node_uw3:
            if node2['ClusterHead'] == ch_node1['NodeID'] and node2['IsSynced'] and node2['NodeID'] != ch_node1['NodeID']:  # Excluir el propio CH
                retries = 0

                while retries < max_retries:
                    
                    start_response_tx_ch = time.time()

                    # Aqui toca agregar el delay de propagación basasdo en la formula de distancia/velocidad
                    # delay = random_sync_delay()  # Generar un tiempo de retraso aleatorio
                    # calcular la distancia entre los nodos
                    dist = np.linalg.norm(ch_node1["Position"] - node2["Position"])
                    
                    start_position = ch_node1["Position"]
                    end_position = node2["Position"]
                    delay = propagation_time(dist, start_position, end_position)
                    
                    print(f"CH {ch_node1['NodeID']} enviando Tx Response_auth_to_sink al nodo {node2['NodeID']} de su cluster, retraso de {delay:.2f} segundos, distancia calculada {dist:.2f}")
                    time.sleep(delay)  # Simular el tiempo de sincronización

                    times_propagation_tx_response = times_propagation_tx_response + (time.time() - start_response_tx_ch)

                    tx_energy = calcular_energia_paquete("tx", es_tx=True)

                    # calculo de energia en la Transmision de la TX_response del CH -> SN
                    ch_node1["ResidualEnergy"] -= tx_energy
                    consumo1 += tx_energy

                    # Captura estadisticas energia
                    stats_proTx2["stats_proTx"][f"CH_Tx{ch_node1['NodeID']}"] = {
                        "energy_consumed": consumo1
                        #"sync_time": sync_end_time_node,
                        #"retransmissions": retries,
                        #"is_syn": node["IsSynced"]
                    }

                    # Medición por cada transmisión CH→Sink
                    # estadisticas nuevas
                    stats["energy"]["CH"]["tx"].append(tx_energy)  # CH trasmite
                    stats["times"]["propagation"].append(delay)
                    stats["attempts"] += retries  # Contar reintentos

                    if propagate_with_probability():
                        # Los nodos que reciben la Tx de respuesta del CH, tambien deben buscar la clave en la bbd y verificarl
                        # print(f"El nodo sensor {node['NodeID']} recibio la Tx del CH {ch['NodeID']}...")

                        payload = auth_response_tx1['Payload']
                        # Dividir el payload por el separador ";"
                        payload_parts = payload.split(';') # obtener el identificador de la firma utilizada
                        id_pair_keys_sign = payload_parts[1] # Obtener el identificador del par de firmas (segundo elemento)

                        # Si la tx llega al nodo debe identificar la id de la clave utilizada para validar la firma
                        _, key_public_sign = load_keys_sign_withou_cipher("bbdd_keys_shared_sign_cipher.db", "keys_sign_ed25519", index=id_pair_keys_sign)
                        
                        rx_energy = calcular_energia_paquete("tx", es_tx=False)
                        
                        # calculo de energia en la Recepción de la TX_response del CH -> SN
                        node2["ResidualEnergy"] -= rx_energy
                        
                        # Captura estadisticas energia
                        stats_proTx2["stats_proTx"][f"Node_Rx{node2['NodeID']}"] = {
                            "energy_consumed": rx_energy
                            #"sync_time": sync_end_time_node,
                            #"retransmissions": retries,
                            #"is_syn": node["IsSynced"]
                        }

                        # Medición por cada transmisión CH→Sink
                        # estadisticas nuevas
                        stats["energy"]["SN"]["rx"].append(rx_energy)  # Nodo recibe

                        # El nodo verifica la tx de autenticación creada y enviada por el CH
                        # Esta se verifica con la clave publica obtenida de la BBDD.
                        if verify_transaction_signature(auth_response_tx1['ID'], auth_response_tx1['Signature'], key_public_sign):
                            print(f"Nodo {node2['NodeID']} recibió y verifico la Tx Response_auth_to_sink de CH {ch_node1['NodeID']}")
                            
                            # Se actualiza el ID del tip en el nodo
                            node2['Tips'].append(auth_response_tx1['ID']) # corregido

                            break
                        else:
                            print(f"Nodo {node2['NodeID']} falló en la verificación de la Tx de autenticación.")
                            retries += 1
                            time.sleep(timeout)
                    else:
                        print(f"Nodo {node2['NodeID']} no recibió la Tx de autenticación. Reintentando... ({retries + 1}/{max_retries})")
                        retries += 1
                        time.sleep(timeout)
                if retries == max_retries:
                    print(f"Nodo {node2['NodeID']} no respondió tras {max_retries} reintentos.")

    return times_response_all_ch, times_propagation_tx_response, stats_proTx2, stats

# Filtrado de Nodos Sincronizados: Primero se filtran los nodos que deben autenticarse con el CH, asegurando que sean nodos sincronizados y que no sean el propio CH.
# Generación de la Transacción: Los nodos generan una transacción de autenticación que envían al CH.
# Verificación del CH: El CH verifica si el nodo está sincronizado y procede a validar la firma con la clave pública obtenida de la base de datos.
# Actualización del Estado del CH: Si la autenticación es exitosa, el CH registra la autenticación del nodo. Si no, el proceso puede reintentarse hasta alcanzar el máximo de intentos.

# Función para propagar la tx de respuesta de los nodos de cada cluster
# SN -> CH
def authenticate_nodes_to_ch(nodes, chead, max_retries=3, timeout=2):
    """
    Función para que los nodos del clúster generen una Tx de autenticación y la envíen al CH.
    nodes: Diccionario con los nodos de la red.
    chead: Nodo CH que recibe las transacciones de autenticación.
    max_retries: Número máximo de reintentos.
    timeout: Tiempo de espera entre reintentos.
    """
    # auth_stats = {
    #     "per_node": {},
    #     "total_energy": 0.0
    # }

    print('El ch que se pasa : ', chead)

      # Diccionario para capturar estadísticas individuales
    stats_proTx3 = {
        "stats_proTx": {},  # Para guardar estadísticas por cada CH y nodo
    }

    consumo2 = 0.0 

    for index_ch in chead:
        print('index_ch : ', index_ch)
        # Filtrar los nodos que tienen a este CH como su ClusterHead y están sincronizados, excluyendo al propio CH
        cluster_nodes = [node3 for node3 in nodes if node3['ClusterHead'] == nodes[index_ch]['NodeID'] and node3['IsSynced'] and node3['NodeID'] != nodes[index_ch]['NodeID']]

        print('Nodos sincronizados : ', cluster_nodes)
        
        # Almacena el node ch para esta vuelta
        node_ch = nodes[index_ch]
        print('Nodo ch para esta vuelta: ', node_ch)

        # Creamos el diccionario para las busquedas rapidas de ID del nodo a actulizar en el CH
        diccionary_nodes = create_diccionary_nodes(node_ch['RegisterNodes'])

        for node4 in cluster_nodes:

            # node_stats = {
            #     "tx_attempts": 0,
            #     "energy_consumed": 0.0
            # }

            retries = 0
            authenticated = False

            print('Nodo del cluster : ', node4)
            # Crear transacción de autenticación para el CH
            node_auth_tx = create_auth_response_tx(node4)

            # Agregar la tx como tips en el nodo, se agrega aqui despues de todo el proceso
            node4['Tips'].append(node_auth_tx['ID'])    # corregido

            while retries < max_retries and not authenticated:

                print(f"Nodo {node4['NodeID']} intenta autenticarse con el CH {node_ch['NodeID']}...")

                # Aqui toca agregar el delay de propagación basasdo en la formula de distancia/velocidad
                # delay = random_sync_delay()  # Generar un tiempo de retraso aleatorio
                # calcular la distancia entre los nodos
                dist = np.linalg.norm(node_ch["Position"] - node4["Position"])
                
                start_position = node4["Position"]
                end_position = node_ch["Position"]
                delay = propagation_time(dist, start_position, end_position)

                print(f"Nodo {node4['NodeID']} envia Tx Response_auth_to_ch al CH {node_ch['NodeID']}, retraso de {delay:.2f} segundos, distancia calculada {dist:.2f}")
                time.sleep(delay)  # Simular el tiempo de sincronización
                
                tx_energy = calcular_energia_paquete("tx", es_tx=True)

                # calculo de energia en la Transmision de la TX_response del SN -> CH
                node4["ResidualEnergy"] -= tx_energy

                # Captura estadisticas energia
                stats_proTx3["stats_proTx"][f"Node_Tx{node4['NodeID']}"] = {
                "energy_consumed": tx_energy
                #"sync_time": sync_end_time_node,
                #"retransmissions": retries,
                #"is_syn": node["IsSynced"]
                }

                # Cálculo de energía por intento
                # estadisticas nuevas
                stats["energy"]["SN"]["tx"].append(tx_energy)  # SN trasmite
                stats["times"]["propagation"].append(delay)
                stats["attempts"] += retries  # Contar reintentos


                if propagate_with_probability():
                    # CH recibe la transacción y verifica si el nodo está sincronizado
                    if node4['IsSynced']:
                        # Dividir el payload para obtener el identificador de la firma
                        payload = node_auth_tx['Payload']
                        payload_parts = payload.split(';')
                        id_pair_keys_sign = payload_parts[1]

                        # Cargar la clave pública desde la base de datos usando el identificador
                        _, key_public_sign = load_keys_sign_withou_cipher("bbdd_keys_shared_sign_cipher.db", "keys_sign_ed25519", index=id_pair_keys_sign)

                        rx_energy = calcular_energia_paquete("tx", es_tx=False)

                        # calculo de energia en la Recepción de la TX_response del SN -> CH
                        node_ch["ResidualEnergy"] -= rx_energy
                        consumo2 += rx_energy

                        # Captura estadisticas energia
                        stats_proTx3["stats_proTx"][f"CH_Rx{node_ch['NodeID']}"] = {
                            "energy_consumed": consumo2
                            #"sync_time": sync_end_time_node,
                            #"retransmissions": retries,
                            #"is_syn": node["IsSynced"]
                        }

                        # estadisticas nuevas
                        stats["energy"]["CH"]["rx"].append(tx_energy)  # SN trasmite

                        # Verificar la transacción con la clave pública
                        if verify_transaction_signature(node_auth_tx['ID'], node_auth_tx['Signature'], key_public_sign):
                            print(f"CH {node_ch['NodeID']} recibió y verificó la Tx Response_auth_to_ch del Nodo {node4['NodeID']}.")

                            node4['Authenticated'] = True  # Se autentica exitosamente
                            authenticated = True

                            # # # Asegurarse de que 'Tips' sea una lista
                            # # if isinstance(node_uw[index_ch]['Tips'], str):
                            # #     node_uw[index_ch]['Tips'] = node_uw[index_ch]['Tips'].split(',')  # Convertir en lista separada por comas si es necesario

                            # # Debe agregar las Tx que son recibidas de los nodos del cluster
                            # # Las agrega como tips
                            # print('Tips del CH definido en ese momento : ', node_uw[index_ch]['Tips'])
                            print("Tx agregada al Tips :", node_auth_tx['ID'])

                            # # Se agrega el id de tx al ch
                            # node_ch['Tips'].append(node_auth_tx['ID'])
                            
                            #nodes[index_ch]['ApprovedTransactions'].append(node_auth_tx['ID'])
                            print("Tx agregadas : ", node_ch['Tips'])
                            #print("Pausa")
                            #time.sleep(5)                        

                            # Se agrega el id de tx al ch
                            node_ch['Tips'].append(node_auth_tx['ID'])  # corregido

                            # # Aqui se debe actualizar las tx del CH
                            # update_transactions(node_ch, node_auth_tx)

                            # Actualizar el nodo dentro del cluster
                            update_transactions(node4, node_auth_tx)    # corregido

                            # #node4['Tips'] = node_auth_tx['ID']
                            # # Buscar la ubicación del nodo en la lista de RegisterNodes
                            # index_node = find_node_index(node_ch['RegisterNodes'], node4['NodeID'])
                            # # print('Indice encontrado: ', index_node)
                            # # time.sleep(5)

                            index_node = diccionary_nodes.get(node4['NodeID'], -1)
                            if index_node != -1:
                                # Aqui debemos colocar como autenticado el nodo en los registros del CH
                                node_ch['RegisterNodes'][index_node]['Status_auth'] = True
                                print(f"El nodo con NodeID {node4['NodeID']} se encuentra en el índice {index_node}.")
                            else:
                                print(f"No se encontró el nodo con NodeID {node4['NodeID']}.")

                            # # Aqui debemos colocar como autenticado el nodo en los registros del CH
                            # node_ch['RegisterNodes'][index_node]['Status_auth'] = True
                            # print('Nodo actualizado : ', node_ch['RegisterNodes'][index_node]['Status_auth'])
                            # time.sleep(5)

                        else:
                            print(f"CH {node_ch['NodeID']} falló en la verificación de la autenticación de Nodo {node4['NodeID']}.")
                            retries += 1
                            time.sleep(timeout)
                    else:
                        print(f"El Nodo {node4['NodeID']} no está sincronizado con el CH {node_ch['NodeID']}. No se puede autenticar.")
                        break
                else:
                    print(f"CH {node_ch['NodeID']} no recibió la Tx de autenticación. Reintentando... ({retries + 1}/{max_retries})")
                    retries += 1
                    time.sleep(timeout)


            if retries == max_retries:
                print(f"CH {node_ch['NodeID']} no autenticó al Nodo {node4['NodeID']} tras {max_retries} reintentos.")
    #print("Que valor tiene : ", node_auth_tx)
    return stats_proTx3, stats

# def update_transactions2(node, approved_tx_ids):
#     """
#     Actualiza las listas de transacciones de un nodo, moviendo las transacciones aprobadas de 'Tips' a 'ApprovedTransactions'.
#     Parameters:
#     - node (dict): Diccionario que representa el nodo con sus transacciones.
#     - approved_tx_ids (list): Lista de IDs de transacciones aprobadas para mover.
#     Returns:
#     - None
#     """
#     # Verificar si hay tips para aprobar
#     if "Tips" in node and "ApprovedTransactions" in node:
#         # Filtrar las transacciones aprobadas
#         for tx_id in approved_tx_ids:
#             if tx_id in node["Tips"]:
#                 # Mover de Tips a ApprovedTransactions
#                 node["ApprovedTransactions"].append(tx_id)
#                 node["Tips"].remove(tx_id)

#         print(f"Nodo {node['NodeID']}: Transacciones actualizadas.")
#     else:
#         print(f"Error: Nodo {node['NodeID']} no tiene listas de transacciones adecuadas.")

# # Ejemplo de uso:
# nodo_ejemplo = {
#     "NodeID": 1,
#     "Tips": ["tx1", "tx2", "tx3"],
#     "ApprovedTransactions": []
# }

# transacciones_aprobadas = ["tx1", "tx3"]
# update_transactions(nodo_ejemplo, transacciones_aprobadas)

# print(nodo_ejemplo)


# def update_transactions(node, received_transaction):
#     """
#     Actualiza la lista de transacciones aprobadas del nodo, moviendo las transacciones de "Tips" a "ApprovedTransactions".
#     Además, verifica las transacciones aprobadas desde la transacción recibida.
#     node: Diccionario del nodo.
#     received_transaction: Transacción recibida que contiene detalles de aprobaciones.
#     """
#     print('Nodo que se va a actualizar : ', node)

#     # Extraer ID de la transacción recibida y las aprobaciones
#     transaction_id = received_transaction.get("ID")
#     approved_tips = received_transaction.get("ApprovedTx", [])

#     # Validar que approved_tips sea una lista
#     if not isinstance(approved_tips, list):
#         print(f"Error: La transacción recibida tiene un campo 'ApprovedTx' inválido: {approved_tips}")
#         return

#     print ('Tips que se deben aprobar : ', approved_tips)

#     # Verificar las transacciones aprobadas y moverlas
#     for tip in approved_tips:
#         print('Tips a mover :', tip)
#         if tip in node["Tips"]:
#             # Mover de Tips a ApprovedTransactions
#             node["Tips"].remove(tip)
#             #verificar duplicados
#             if tip not in node["ApprovedTransactions"]:
#                 node["ApprovedTransactions"].append(tip)
#             else:
#                 print('El tips ya esta agregado...')

#     # # Agregar la transacción recibida a ApprovedTransactions
#     # if transaction_id not in node["Tips"]:
#     #     node["Tips"].append(transaction_id)

#     print('Nodo actualizado en sus ApprovedTx : ', node["ApprovedTransactions"], ' -> ID : ', node['NodeID'])

# # Ejemplo de uso
# nodo_ejemplo = {
#     "NodeID": 1,
#     "Tips": ["tx4", "tx5", "tx6"],
#     "ApprovedTransactions": []
# }

# # Ejemplo de transacción recibida que aprueba otras transacciones
# transaccion_recibida = {
#     "ID": "tx7",
#     "ApprovedTransactions": ["tx4", "tx5"]
# }

# update_transactions(nodo_ejemplo, transaccion_recibida)
# print(nodo_ejemplo)


# Nueva función de update_transactions
import copy

def update_transactions(node, received_transaction):
    """
    Actualiza la lista de transacciones del nodo, moviendo Tips a ApprovedTransactions.
    Además, trabaja con una copia de la transacción recibida para evitar modificar la original.
    node: Diccionario del nodo.
    received_transaction: Transacción recibida que contiene detalles de aprobaciones.
    """
    print('Nodo que se va a actualizar : ', node["NodeID"])

    # Hacer una copia profunda de la transacción recibida para evitar modificar la original
    transaction_copy = copy.deepcopy(received_transaction)

    # Extraer ID de la transacción recibida y las aprobaciones
    transaction_id = transaction_copy.get("ID")
    # approved_tips2 = transaction_copy.get("ApprovedTx", [])
    # approved_tips2 = transaction_copy.get("ApprovedTx")
    # approved_tips2 = transaction_copy.setdefault("ApprovedTx", [])
    # approved_tips2 = received_transaction["ApprovedTx"]
    approved_tips2 = list(received_transaction.get("ApprovedTx", []))

    print('Tips que se deben aprobar 1: ', transaction_copy)
    print('Tips que se deben aprobar 2: ', approved_tips2)

    # Copiar Tips del nodo para iterar sin alterar la lista directamente
    tips_to_check = list(node["Tips"])

    # Verificar las transacciones aprobadas y moverlas
    for tip in approved_tips2:
        if tip in tips_to_check:
            # Mover de Tips a ApprovedTransactions
            node["Tips"].remove(tip)  # Eliminar el tip de la lista de Tips del nodo
            if tip not in node["ApprovedTransactions"]:  # Prevenir duplicados
                node["ApprovedTransactions"].append(tip)

    # # Agregar la copia de la transacción recibida al campo "Transactions" del nodo
    # if transaction_id not in [tx["ID"] for tx in node["Transactions"]]:
    #     node["Transactions"].append(transaction_copy)

    # La transacción original permanece intacta
    print('Nodo actualizado en ApprovedTransactions:', node["ApprovedTransactions"])
    print('Tips restantes:', node["Tips"])



# Funcion para eliminar la tx
def delete_transaction(node, transaction_id):
    """
    Elimina una transacción del nodo dado su ID.
    
    Args:
        node (dict): Nodo del que se desea eliminar la transacción.
        transaction_id (str): ID de la transacción a eliminar.

    Returns:
        bool: True si la transacción fue eliminada, False si no se encontró.
    """
    transactions = node.get("Transactions", [])
    
    for tx in transactions:
        if tx["ID"] == transaction_id:
            transactions.remove(tx)
            print(f"Transacción con ID {transaction_id} eliminada del nodo {node['NodeID']}.")
            return True

    print(f"Transacción con ID {transaction_id} no encontrada en el nodo {node['NodeID']}.")
    return False


# Función para busqueda lineal en el diccionario, no puede ser muy eficiente si incrementa el numero de nodos
def find_node_index(register_nodes, target_node_id):
    """
    Busca en la lista 'register_nodes' el nodo cuyo 'NodeID' coincide con 'target_node_id'
    y devuelve su índice. Si no se encuentra el nodo, retorna -1.

    Parámetros:
      - register_nodes: lista de diccionarios, cada uno representando un nodo.
      - target_node_id: identificador del nodo a buscar (se compara en forma de cadena).

    Retorna:
      - Índice (int) del nodo en la lista, o -1 si no se encontró.
    """
    # Convertir el target_node_id a cadena para evitar problemas de tipado
    target_node_id = str(target_node_id)
    
    # print('Register nodes: ', register_nodes)
    # print('Target node id : ', target_node_id)

    # Realiza una búsqueda lineal en la lista
    for index, node in enumerate(register_nodes):
        # print('Indice : ', index, ' node : ', node)
        # time.sleep(5)
        if str(node.get("NodeID")) == target_node_id:
            return index  # Se retorna el índice tan pronto se encuentra la coincidencia
    return -1  # Retorna -1 si no se encontró ningún nodo con el ID especificado


# Función para busquedas más rapidas, conviertiendo los indices y el nodoId en un diccionario para busquedas
def create_diccionary_nodes(register_nodes):
    """
    Crea un diccionario que asocia cada NodeID al índice correspondiente.
    
    Parámetros:
      - register_nodes: lista de diccionarios, cada uno representando un nodo.
    
    Retorna:
      - Un diccionario {NodeID: índice}
    """
    return {node["NodeID"]: index for index, node in enumerate(register_nodes)}