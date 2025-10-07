from tangle2_light import create_gen_block, create_transaction, sign_transaction, verify_transaction_signature
from bbdd2_sqlite3 import load_keys_shared_withou_cipher, load_keys_sign_withou_cipher
from path_loss import propagation_time1
import numpy as np
from energia_dinamica import calcular_energia_paquete, energy_listen, energy_standby, calculate_timeout, update_energy_node_tdma, update_energy_standby_others, update_energy_failed_rx, estimate_proc_time_s
from per_from_link_uan import per_from_link, propagate_with_probability
from transmission_logger_uan import log_event
import random
import time

PER_VARIABLE = None

### agregado 28/09/2025
# --- Componentes de latencia (todo en ms) ---
# from path_loss import propagation_time1

def prop_delay_ms(start_pos, end_pos, depth=None, region="standard") -> float:
    return float(propagation_time1(start_pos, end_pos, depth, region)) * 1000.0

def tx_time_ms(bits: int, bitrate: int) -> float:
    return (bits / max(1, bitrate)) * 1000.0

def proc_time_ms(fixed_ms: float = 20.0) -> float:
    return float(fixed_ms)
####

# import pickle

# # Cargas nodos y sink
# # Para cargar la estructura de nodos guardada
# with open('nodos_guardados.pkl', 'rb') as file:
#     node_uw = pickle.load(file)

# # Para cargar la estructura de nodos guardada
# with open('sink_guardado.pkl', 'rb') as file:
#     nodo_sink = pickle.load(file)

# # print(nodo_sink)
# Consideramos un escenario ideal donde todas las Tx llegan a su destino
# success_rate = 0

# Se comenta para mejoras
# # # def propagate_with_probability(success_rate = 0):
# # #     """
# # #     Simula la probabilidad de éxito de la propagación de una transacción.
# # #     Parameters:
# # #     success_rate: Probabilidad de éxito en la propagación de la transacción (por defecto 80%).
# # #     Returns:
# # #     True si la propagación es exitosa (según el valor aleatorio y la tasa de éxito), False en caso contrario.
# # #     """
# # #     return random.random() > success_rate

# --- [ADD] helpers para mantener consistencia del DAG local ---
def tips_add(node, tx_id):
    if tx_id not in node.get("Tips", []):
        node["Tips"].append(tx_id)

def tips_remove(node, tx_id):
    if tx_id in node.get("Tips", []):
        node["Tips"].remove(tx_id)

def approved_add(node, tx_id):
    if tx_id not in node.get("ApprovedTransactions", []):
        node["ApprovedTransactions"].append(tx_id)

## Sugenrencia de update_transactios
# def update_transactions(node, received_transaction):
#     """
#     Mueve tips aprobados a 'ApprovedTransactions' y añade la tx recibida como nueva tip.
#     Evita duplicados.
#     """
#     tx_id = received_transaction.get("ID")
#     approved = list(received_transaction.get("ApprovedTx", []))
#     for tip in approved:
#         tips_remove(node, tip)
#         approved_add(node, tip)
#    tips_add(node, tx_id)


table_events = []

# Funcion para propagar tx genesis hacia los CHs
# Los Ch deben validar la tx enviada por el genesis
# Sink -> CH
def propagate_tx_to_ch(RUN_ID, sink1, ch_list, node_uw1, genesis_tx, E_schedule, ronda, max_retries=3, timeout=2):
    """
    Función para propagar la transacción génesis del Sink a los CHs.
    Si un CH no responde en el tiempo establecido, se reintenta la propagación.
    sink1: Estructura del Sink.
    ch_list: Lista de CHs a los que se propagará la Tx génesis.
    genesis_tx: Transacción génesis creada por el Sink.
    max_retries: Número máximo de reintentos.
    timeout: Tiempo de espera entre reintentos.
    """
    energy_consumed_ch_rx = energy_consumed_ch_tx = 0
    initial_energy_ch_rx = initial_energy_ch_tx = 0
    timeout_sinktoch = 0

    # Listas para almacenar los tiempos de verificación y respuesta por cada CH
    # times_verify_all_ch = []
    # speed_propagation = []
    # times_response_all_ch = []
    # times_propagation_tx = 0

    type_packet = "tx"
    type_packet_control = "sync"

    for index_ch in ch_list:
        retries = 0
        retries_ChtoSink = 0
        #node_ch = node_uw[ch]
        # print('INICIO DE PROPGATE : ', node_ch)
        ack_received_SinktoCH = False
        auth_isverify = False
        # Almacena el nodo ch para esta ronda
        Ch_node = node_uw1[index_ch]

        while retries < max_retries and not ack_received_SinktoCH:
            # Verificar si el CH está sincronizado, para poder recibir la Tx
            if Ch_node['IsSynced']:
                # print(f"Propagando Tx génesis al CH {node_uw[ch]['NodeID']}")

                # Aqui toca agregar el delay de propagación basasdo en la formula de distancia/velocidad
                # calcular la distancia entre los nodos
                dist = np.linalg.norm(Ch_node["Position"] - sink1["Position"])  # se debe comentar 10/09/2025

                # calular el per
                per_sink_ch_auth, SL_db, snr_db, EbN0_db, ber = per_from_link(f_khz=20, distance_m=dist, L=1600, bitrate=9200)

                start_position = sink1["Position"]
                end_position = Ch_node["Position"]

                #delay = propagation_time(dist, start_position, end_position)    # se comenta 10/09/2025
                delay = propagation_time1(start_position, end_position, depth=None, region="standard")
                print(f"Sink enviando Tx genesis (Request_auth) al CH {Ch_node['NodeID']}, retraso de {delay:.2f} segundos, distancia calculada {dist:.2f}")
                # time.sleep(delay)  # Simular el tiempo de sincronización

                success_auth = propagate_with_probability(per=per_sink_ch_auth, override_per=PER_VARIABLE)
                p_lost_auth = not success_auth
                bits_sent_auth = 1600 # bits
                bits_received_auth = 1600 if success_auth else 0

                # speed_propagation.append(speed)
                # print('speed_propagation', speed_propagation)
                # times_propagation_tx = times_propagation_tx + (time.time() - time_start_ptx)
                # times_propagation_tx = delay

                # Simular probabilidad de recepción
                if success_auth:
                    ack_received_SinktoCH = True
                    # Verificar la Tx con la clave pública del Sink
                    # calcular el tiempo de verificación tx por parte del CH
                    time_start = time.perf_counter()
                    isverify = verify_transaction_signature(genesis_tx, genesis_tx['Signature'], Ch_node['PublicKey_sign_sink'])
                    end_time_verify = (time.perf_counter() - time_start)*1000 # se la obtiene en milisegundos
                    # times_verify_all_ch.append(end_time_verify)  # Guardar el tiempo de verificación para este CH

                    # CH recibe y verifica génesis
                    t_proc_ch_recv_gen = estimate_proc_time_s(do_verify=True, do_tips=True)

                    # guardar la energía antes de actualizar
                    initial_energy_ch_rx = Ch_node["ResidualEnergy"]

                    # Calcular el timeout de espera
                    lat_prop, lat_tx, lat_proc, timeout_sinktoch = calculate_timeout(start_position, end_position, bitrate=9200, packet_size=bits_sent_auth, proc_time_s=t_proc_ch_recv_gen)

                    # Actualiza energía del nodo
                    Ch_node = update_energy_node_tdma(Ch_node, sink1["Position"], E_schedule,
                                                   timeout_sinktoch, type_packet, role='CH', action='rx', verbose=True, t_verif_s=t_proc_ch_recv_gen)

                    energy_consumed_ch_rx = ((initial_energy_ch_rx - Ch_node["ResidualEnergy"]))
                    print(f'Energy consumed del CH en Rx : ', energy_consumed_ch_rx)

                    # Se almacena en log_event
                    log_event(
                            run_id=RUN_ID, phase="auth", module="tangle", msg_type="AUTH:GEN",
                            sender_id=sink1["NodeID"], receiver_id=Ch_node["NodeID"], cluster_id=Ch_node["ClusterHead"],
                            start_pos=start_position, end_pos=end_position,
                            bits_sent=bits_sent_auth, bits_received=bits_received_auth,
                            success=success_auth, packet_lost=p_lost_auth,
                            energy_event_type='rx', energy_j=energy_consumed_ch_rx,
                            residual_sender=None, residual_receiver=Ch_node["ResidualEnergy"],
                            bitrate=9200, freq_khz=20,
                            lat_prop_ms=lat_prop, lat_tx_ms=lat_tx, lat_proc_ms=t_proc_ch_recv_gen,
                            snr_db=snr_db, per=per_sink_ch_auth,
                            lat_dag_ms=0.0, SL_db=SL_db, EbN0_db=EbN0_db, BER=ber
                        )

                    # Sink to CH
                    # Verifcar la tx recibida del Sink
                    if isverify:
                        auth_isverify = True
                        print(f"CH {Ch_node['NodeID']} recibió y verificó la Tx génesis.")
                        Ch_node['Tips'].append(genesis_tx['ID'])    # Se guarda la Tx genesis en el CH

                        ack_received_CHtoSink = False  # aún no confirmado

                        while retries_ChtoSink < max_retries and not ack_received_CHtoSink:
                            # Confirma la recepción de la Tx
                            # guardar la energía antes de actualizar
                            initial_energy_ch_tx = Ch_node["ResidualEnergy"]

                            # calular el per
                            per_ch_sink_auth_ack, SL_db, snr_db, EbN0_db, ber = per_from_link(f_khz=20, distance_m=dist, L=48, bitrate=9200)

                            success_auth_ack = propagate_with_probability(per=per_ch_sink_auth_ack, override_per=PER_VARIABLE)
                            p_lost_auth_ack = not success_auth_ack
                            bits_sent_auth_ack = 48 # bits
                            bits_received_auth_ack = 48 if success_auth_ack else 0

                            # Calcular el timeout de espera
                            lat_prop, lat_tx, lat_proc, timeout_chtosink = calculate_timeout(start_position, end_position, bitrate=9200, packet_size=48)

                            # Actualiza energía del nodo
                            Ch_node = update_energy_node_tdma(Ch_node, sink1["Position"], E_schedule,
                                                        timeout_chtosink, type_packet_control, role='CH', action='tx', verbose=True)
                            energy_consumed_ch_tx = ((initial_energy_ch_tx - Ch_node["ResidualEnergy"]))
                            print(f'Energy consumed del CH en Tx ACK : ', energy_consumed_ch_tx)

                            # Se almacena en log_event
                            log_event(
                                    run_id=RUN_ID, phase="auth", module="tangle", msg_type="AUTH:GEN:ACK",
                                    sender_id=Ch_node["NodeID"], receiver_id=sink1["NodeID"], cluster_id=Ch_node["ClusterHead"],
                                    start_pos=start_position, end_pos=end_position,

                                    bits_sent=bits_sent_auth_ack, bits_received=bits_received_auth_ack,
                                    success=success_auth_ack, packet_lost=p_lost_auth_ack,
                                    energy_event_type='tx', energy_j=energy_consumed_ch_tx,
                                    residual_sender=Ch_node["ResidualEnergy"], residual_receiver=None,
                                    bitrate=9200, freq_khz=20,
                                    lat_prop_ms=lat_prop, lat_tx_ms=lat_tx, lat_proc_ms=lat_proc,
                                    snr_db=snr_db, per=per_ch_sink_auth_ack,
                                    lat_dag_ms=0.0, SL_db=SL_db, EbN0_db=EbN0_db, BER=ber
                                )

                            if success_auth_ack:
                                ack_received_CHtoSink = True
                                print(f"CH {Ch_node['NodeID']} envió correctamente el ACK de la Tx génesis.")
                            else:
                                retries_ChtoSink += 1
                                print(f"El {sink1['NodeID']} no recibió el ack de la Tx génesis. Reintentando...")

                            # Se actualiza la energia de los demas nodos
                            active_ids = [Ch_node["NodeID"]]
                            node_uw1 = update_energy_standby_others(node_uw1, active_ids, timeout_chtosink, verbose=True)

                            # # Ch to Sink
                            # Propagar la Tx Génesis a los nodos del cluster del CH
                            # CH -> SN
                            propagate_genesis_to_cluster(RUN_ID, node_uw1, index_ch, genesis_tx,
                                                         E_schedule, ronda, max_retries=3, timeout=2)
                        # recived = True
                        # break
                    else:
                        print(f"CH {Ch_node['NodeID']} falló en la verificación de la Tx génesis.")
                        # recived = False
                        # break
                else:
                    print(f"CH {Ch_node['NodeID']} no recibió la Tx génesis. Reintentando...")
                    retries += 1
                    # Actualiza la energía del nodo en caso de no recibir el pkt, pero esta escuchando en su slot
                    Ch_node = update_energy_failed_rx(Ch_node, sink1["Position"], timeout_sinktoch, role="CH", verbose=False)
                    # time.sleep(timeout)

                # Se actualiza la energia de los demas nodos exista o no recepción del mensaje en el nodo
                active_ids = [Ch_node["NodeID"]]
                node_uw1 = update_energy_standby_others(node_uw1, active_ids, timeout_sinktoch, verbose=True)

            else:
                print(f"CH {Ch_node['NodeID']} no está sincronizado. Omitido.")
                # recived = False
                # break
        if retries == max_retries:
            print(f"CH {Ch_node['NodeID']} no respondió tras {max_retries} reintentos.")
            # recived = False
    return

#############################
# Funcion para propagar la tx genesis hacia cada cluster
# CH -> SN
def propagate_genesis_to_cluster(RUN_ID, node_uw2, ch_index, genesis_tx, E_schedule, ronda, max_retries=3, timeout=2):
    """
    Propaga la Tx Génesis desde el CH a los nodos sincronizados en su cluster con reintentos.
    node_uw: Diccionario de los nodos.
    ch_index: Índice del CH que está propagando la transacción.
    genesis_tx: Transacción génesis creada por el Sink.
    max_retries: Número máximo de reintentos.
    timeout: Tiempo de espera entre reintentos (en segundos).
    """
    # CONTADOR_EVENTOS = 0
    energy_consumed_ch_tx = energy_consumed_ch_rx = 0
    energy_consumed_sn_tx = energy_consumed_sn_rx = 0
    initial_energy_ch_tx = initial_energy_ch_rx = 0
    initial_energy_sn_tx = initial_energy_sn_rx = 0

    type_packet = "tx"
    type_packet_control = "sync"

    print('Iniciando propagación de la transacción génesis dentro del cluster...')
    indexCH = node_uw2[ch_index]['NodeID']

    # Almacena el nodo CH para esta ronda
    ch_node1 = node_uw2[ch_index]
    #print(indexCH)

    # Variable para almacenar el tiempo de propagación de tx genesis
    # times_propagation_tx_nodes = 0

    # Iterar sobre los nodos del cluster
    for node1 in node_uw2:
        ack_received_SN = False
        # print(node)
        # Verificar si el nodo pertenece al cluster del CH y está sincronizado
        #print('Nodo for : ', node['NodeID'], 'Nodo estrutura node_uw : ', node_uw[ch_index]['NodeID'])
        if node1['NodeID'] != indexCH and node1['IsSynced'] and node1['ClusterHead'] == indexCH:
            retries = 0
            while retries < max_retries and not ack_received_SN:
                # print(f"Intentando enviar la transacción génesis al nodo {node['NodeID']}... Reintento {retries + 1}/{max_retries}")

                # calcular la distancia entre los nodos
                dist = np.linalg.norm(ch_node1["Position"] - node1["Position"]) # Se debe comentar 10/09/2025

                start_position = ch_node1["Position"]
                end_position = node1["Position"]
                # delay = propagation_time(dist, start_position, end_position)    # se comenta 10/09/2025
                delay = propagation_time1(start_position, end_position, depth=None, region="standard")

                print(f"CH {ch_node1['NodeID']} enviando Tx genesis (Request_auth) al nodo {node1['NodeID']}, retraso de {delay:.2f} segundos, distancia calculada {dist:.2f}")
                # time.sleep(delay)  # Simular el tiempo de sincronización
                # speed_propagation.append(speed)
                # times_propagation_tx_nodes = times_propagation_tx_nodes + (time.time() - time_start_ptx)
                # times_propagation_tx_nodes = delay

                # guardar la energía antes de actualizar
                initial_energy_ch_tx = ch_node1["ResidualEnergy"]
                # Calcular el timeout de espera
                lat_prop, lat_tx, lat_proc, timeout_ch_to_sn = calculate_timeout(start_position, end_position, bitrate=9200, packet_size=1600)
                # Actualiza energía del nodo
                ch_node1 = update_energy_node_tdma(ch_node1, node1["Position"], E_schedule,
                                                    timeout_ch_to_sn, type_packet, role='CH', action='tx', verbose=True)

                energy_consumed_ch_tx = ((initial_energy_ch_tx - ch_node1["ResidualEnergy"]))
                print(f'Energy consumed del CH en Tx - Tx-genesis : ', energy_consumed_ch_tx)

                per_ch_to_sn, SL_db, snr_db, EbN0_db, ber = per_from_link(f_khz=20, distance_m=dist, L=1600, bitrate=9200)

                success_auth = propagate_with_probability(per=per_ch_to_sn, override_per=PER_VARIABLE)
                p_lost_auth = not success_auth
                bits_sent_auth = 1600 # bits
                bits_received_auth = 1600 if success_auth else 0

                # Se almacena en log_event tx del msj de auth-genesis-sink
                log_event(
                        run_id=RUN_ID, phase="auth", module="tangle", msg_type="AUTH:GEN",
                        sender_id=ch_node1["NodeID"], receiver_id=node1["NodeID"], cluster_id=node1["ClusterHead"],
                        start_pos=start_position, end_pos=end_position,
                        bits_sent=bits_sent_auth, bits_received=bits_received_auth,
                        success=success_auth, packet_lost=p_lost_auth,
                        energy_event_type='tx', energy_j=energy_consumed_ch_tx,
                        residual_sender=ch_node1["ResidualEnergy"], residual_receiver=node1["ResidualEnergy"],
                        bitrate=9200, freq_khz=20,
                        lat_prop_ms=lat_prop, lat_tx_ms=lat_tx, lat_proc_ms=lat_proc,
                        snr_db=snr_db, per=per_ch_to_sn,
                        lat_dag_ms=0.0, SL_db=SL_db, EbN0_db=EbN0_db, BER=ber
                    )

                # Se actualiza la energia de los demas nodos
                active_ids = [ch_node1["NodeID"],node1["NodeID"]]
                node_uw2 = update_energy_standby_others(node_uw2, active_ids, timeout_ch_to_sn, verbose=True)

                # CH to SN
                # confirma la recepción del pkt
                if success_auth:
                    ack_received_SN = True
                    # Verificar la Tx con la clave pública del Sink
                    # calcular el tiempo de verificación tx por parte del CH
                    time_start = time.perf_counter()
                    isverify = verify_transaction_signature(genesis_tx, genesis_tx['Signature'], node1['PublicKey_sign_sink'])
                    end_time_verify = time.perf_counter()- time_start

                    # CH recibe y verifica génesis
                    t_proc_sn_recv_gen = estimate_proc_time_s(do_sign=True, do_tips=True)

                    # Actualizar la energia del SN receptión tx-genesis
                    initial_energy_sn_rx = node1["ResidualEnergy"]
                    # Calcular el timeout de espera
                    lat_prop, lat_tx, _, timeout_ch_to_sn = calculate_timeout(start_position, end_position, bitrate=9200, packet_size=1600, proc_time_s=t_proc_sn_recv_gen)
                    # Actualiza energía del nodo
                    node1 = update_energy_node_tdma(node1, ch_node1["Position"], E_schedule,
                                                        timeout_ch_to_sn, type_packet, role='SN', action='rx', verbose=True, t_verif_s=t_proc_sn_recv_gen)
                    energy_consumed_sn_rx = ((initial_energy_sn_rx - node1["ResidualEnergy"]))
                    print(f'Energy consumed del SN en Rx - Tx-genesis : ', energy_consumed_sn_rx)

                    # Log guarda consumo por recibir auth:gen:sink
                    log_event(
                        run_id=RUN_ID, phase="auth", module="tangle", msg_type="AUTH:GEN",
                        sender_id=ch_node1["NodeID"], receiver_id=node1["NodeID"], cluster_id=node1["ClusterHead"],
                        start_pos=start_position, end_pos=end_position,
                        bits_sent=bits_sent_auth, bits_received=bits_received_auth,
                        success=success_auth, packet_lost=p_lost_auth,
                        energy_event_type='rx', energy_j=energy_consumed_sn_rx,
                        residual_sender=ch_node1["ResidualEnergy"], residual_receiver=node1["ResidualEnergy"],
                        bitrate=9200, freq_khz=20,
                        lat_prop_ms=lat_prop, lat_tx_ms=lat_tx, lat_proc_ms=t_proc_sn_recv_gen,
                        snr_db=snr_db, per=per_ch_to_sn,
                        lat_dag_ms=0.0, SL_db=SL_db, EbN0_db=EbN0_db, BER=ber
                    )

                    # CH to SN

                    # Verificar la Tx con la clave pública del Sink
                    if isverify:
                        retries_SNtoCH = 0
                        ack_received_CH = False

                        while retries_SNtoCH < max_retries and not ack_received_CH:
                            print(f"Nodo {node1['NodeID']} en cluster {ch_node1['NodeID']} recibió y verificó la Tx génesis.")

                            #id_genesis_tx1 = copy.deepcopy(genesis_tx)
                            node1['Tips'].append(genesis_tx['ID'])   # El nodo agrega la Tx genesis propagada por el CH

                            # calular el per
                            per_sn_gen_ack, SL_db, snr_db, EbN0_db, ber = per_from_link(f_khz=20, distance_m=dist, L=48, bitrate=9200)

                            success_gen_ack = propagate_with_probability(per=per_sn_gen_ack, override_per=PER_VARIABLE)
                            p_lost_gen_ack = not success_gen_ack
                            bits_sent_gen_ack = 48 # bits
                            bits_received_gen_ack = 48 if success_gen_ack else 0

                            # Actualizar la energia del SN en Tx del ACK
                            initial_energy_sn_tx = node1["ResidualEnergy"]
                            # Calcular el timeout de espera
                            lat_prop, lat_tx, lat_proc, timeout_sn_to_ch = calculate_timeout(start_position, end_position, bitrate=9200, packet_size=48)
                            # Actualiza energía del nodo
                            node1 = update_energy_node_tdma(node1, ch_node1["Position"], E_schedule,
                                                                timeout_sn_to_ch, type_packet_control, role='SN', action='tx', verbose=True)
                            energy_consumed_sn_tx = ((initial_energy_sn_tx - node1["ResidualEnergy"]))
                            print(f'Energy consumed del SN en Tx - ACK : ', energy_consumed_sn_tx)


                            # Se almacena en log_event de la tx del ack:auth
                            log_event(
                                    run_id=RUN_ID, phase="auth", module="tangle", msg_type="AUTH:GEN:ACK",
                                    sender_id=node1["NodeID"], receiver_id=ch_node1["NodeID"], cluster_id=node1["ClusterHead"],
                                    start_pos=start_position, end_pos=end_position,
                                    bits_sent=bits_sent_gen_ack, bits_received=bits_received_gen_ack,
                                    success=success_gen_ack, packet_lost=p_lost_gen_ack,
                                    energy_event_type='tx', energy_j=energy_consumed_sn_tx,
                                    residual_sender=node1["ResidualEnergy"], residual_receiver=ch_node1["ResidualEnergy"],
                                    bitrate=9200, freq_khz=20,
                                    lat_prop_ms=lat_prop, lat_tx_ms=lat_tx, lat_proc_ms=lat_proc,
                                    snr_db=snr_db, per=per_sn_gen_ack,
                                    lat_dag_ms=0.0, SL_db=SL_db, EbN0_db=EbN0_db, BER=ber
                                    )
                            # Se actualiza la energia de los demas nodos
                            active_ids = [node1["NodeID"], ch_node1["NodeID"]]
                            node_uw2 = update_energy_standby_others(node_uw2, active_ids, timeout_sn_to_ch, verbose=True)

                            if success_gen_ack:
                                ack_received_CH = True
                                # SN to CH

                                # Recepción del paquete ACK del SN
                                # guardar la energía antes de actualizar
                                initial_energy_ch_rx = ch_node1["ResidualEnergy"]
                                # Calcular el timeout de espera
                                lat_prop, lat_tx, lat_proc, timeout_sn_to_ch = calculate_timeout(start_position, end_position, bitrate=9200, packet_size=48)
                                # Actualiza energía del nodo
                                ch_node1 = update_energy_node_tdma(ch_node1, node1["Position"], E_schedule,
                                                                    timeout_sn_to_ch, type_packet_control, role='CH', action='rx', verbose=True)
                                energy_consumed_ch_rx = ((initial_energy_ch_rx - ch_node1["ResidualEnergy"]))
                                print(f'Energy consumed del CH en Tx - Tx-genesis : ', energy_consumed_ch_rx)

                                # Se almacena en log_event de la rx del ack:auth al CH
                                log_event(
                                        run_id=RUN_ID, phase="auth", module="tangle", msg_type="AUTH:GEN:ACK",
                                        sender_id=ch_node1["NodeID"], receiver_id=node1["NodeID"], cluster_id=node1["ClusterHead"],
                                        start_pos=start_position, end_pos=end_position,
                                        bits_sent=bits_sent_gen_ack, bits_received=bits_received_gen_ack,
                                        success=success_gen_ack, packet_lost=p_lost_gen_ack,
                                        energy_event_type='rx', energy_j=energy_consumed_ch_rx,
                                        residual_sender=node1["ResidualEnergy"], residual_receiver=ch_node1["ResidualEnergy"],
                                        bitrate=9200, freq_khz=20,
                                        lat_prop_ms=lat_prop, lat_tx_ms=lat_tx, lat_proc_ms=lat_proc,
                                        snr_db=snr_db, per=per_sn_gen_ack,
                                        lat_dag_ms=0.0, SL_db=SL_db, EbN0_db=EbN0_db, BER=ber
                                        )
                                # SN to CH
                                # break  # Salir del bucle de reintentos si la verificación es exitosa
                            else:
                                retries_SNtoCH += 1
                                print(f"El CH {ch_node1['NodeID']} no recibió el ack de la Tx génesis enviada al SN {node1['NodeID']}. Reintentando...")
                                # Actualiza la energía del nodo en caso de no recibir el pkt, pero esta escuchando en su slot
                                ch_node1 = update_energy_failed_rx(ch_node1, node1["Position"], timeout_sn_to_ch, role="CH", verbose=False)
                    else:
                        print(f"Nodo {node1['NodeID']} falló en la verificación de la Tx génesis.")
                        retries += 1
                        # time.sleep(timeout)
                else:
                    print(f"Nodo {node1['NodeID']} no recibió la Tx génesis. Reintentando... ({retries + 1}/{max_retries})")
                    retries += 1
                    # Actualiza la energía del nodo en caso de no recibir el pkt, pero esta escuchando en su slot
                    node1 = update_energy_failed_rx(node1, ch_node1["Position"], timeout_ch_to_sn, role="SN", verbose=False)
                    # time.sleep(timeout)
            # Si se alcanzan los reintentos máximos
            if retries == max_retries:
                print(f"Nodo {node1['NodeID']} no respondió tras {max_retries} reintentos.")

    return

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

    # print('approved_tips Toma dos tips para generar la Tx de respuesta :', approved_tips1, ' -> ID : ', node_ch1['NodeID'])

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
def propagate_tx_to_sink_and_cluster(RUN_ID, sink1, list_ch, node_uw3, E_schedule, ronda, max_retries=3, timeout=2):
    """
    Propaga la Tx de respuesta de autenticación desde el CH al Sink y a los nodos de su cluster con reintentos.
    node_ch2: Nodo CH que está propagando la transacción.
    sink: Nodo Sink que recibirá la Tx.
    node_uw: Diccionario de los nodos.
    auth_response_tx: Transacción de respuesta de autenticación creada por el CH.
    max_retries: Número máximo de reintentos.
    timeout: Tiempo de espera entre reintentos (en segundos).
    """
    energy_consumed_ch_tx = energy_consumed_ch_rx = 0
    energy_consumed_sn_tx = energy_consumed_sn_rx = 0
    initial_energy_ch_tx = initial_energy_ch_rx = 0
    initial_energy_sn_tx = initial_energy_sn_rx = 0

    #Id_nodeCH = node_ch2['NodeID']
    type_packet = "tx"
    type_packet_control = "sync"
    #print('Nodo que se va actualizar el auth en el sink: ', Id_nodeCH)

    # # Listas para almacenar los tiempos de verificación y respuesta por cada CH
    # times_verify_all_ch = []
    # times_response_all_ch = []

    # Variable para almacenar el tiempo de propagación de tx respuesta del CH
    # al sink y nodos del cluster
    # times_propagation_tx_response = 0
    ack_received_chtosink= False

    for ch_index in list_ch:
        ack_received_chtosink = False

        print('Iniciando propagación de la transacción respuesta del CH al sink y dentro del cluster...')
        indexCH = node_uw3[ch_index]['NodeID']

        # Almacena el nodo CH para esta ronda
        ch_node1 = node_uw3[ch_index]

        # Crear la nueva transacción de respuesta y propagarla al Sink
        # Response_auth_to_sink
        time_start_responseCH = time.perf_counter() # Incia tiempo de medición de la creación de la nueva Tx de response
        auth_response_tx1 = create_auth_response_tx(ch_node1)
        end_time_responseCH = time.perf_counter() - time_start_responseCH
        # times_response_all_ch.append(end_time_responseCH)  # Guardar el tiempo de respuesta para este CH

        # Crear una copia profunda de la transacción para evitar referencias compartidas
        auth_response_tx_sink = deepcopy(auth_response_tx1)
        auth_response_tx_ch = deepcopy(auth_response_tx1)

        # # Actualizar la tx de Tips a ApprovedTransactions del ch
        update_transactions(ch_node1, auth_response_tx_ch)  # corregido

        # Eliminar la tx que genera conflicto, para solucionar la eliminación de tx aprobada
        id_transaction = auth_response_tx_ch['ID']

        # Eliminar la transacción
        delete_transaction(ch_node1, id_transaction) # corregido

        # # Aqui se agrega la TX en el tips del nodo
        ch_node1['Tips'].append(id_transaction)     # corregido

        # Se vuelve agregar la tx en el nodo
        ch_node1['Transactions'].append(auth_response_tx_ch)    # corregido

        retries_ch = retries_sn = 0

        while retries_ch < max_retries and not ack_received_chtosink:
            start_response_tx_ch = time.perf_counter()
            # Se puede medir el tiempo de propagación de la Tx dentro del cluster
            # Aqui toca agregar el delay de propagación basasdo en la formula de distancia/velocidad
            # delay = random_sync_delay()  # Generar un tiempo de retraso aleatorio
            # calcular la distancia entre los nodos
            dist = np.linalg.norm(ch_node1["Position"] - sink1["Position"]) # se debe comentar 10/09/2025

            start_position = ch_node1["Position"]
            end_position = sink1["Position"]
            # delay = propagation_time(dist, start_position, end_position)    # se comenta 10/09/2025
            delay = propagation_time1(start_position, end_position, depth=None, region="standard")
            print(f"CH {ch_node1['NodeID']} enviando Tx Response_auth_to_sink, retraso de {delay:.2f} segundos, distancia calculada {dist:.2f}")
            # time.sleep(delay)  # Simular el tiempo de sincronización

            # times_propagation_tx_response = times_propagation_tx_response + (time.time() - start_response_tx_ch)
            # times_propagation_tx_response = delay

            # calculos de calidad del enlace
            per_resp_auth_ch_sink, SL_db, snr_db, EbN0_db, ber = per_from_link(f_khz=20, distance_m=dist, L=1600, bitrate=9200)

            # CH crea y firma tx de respuesta
            t_proc_ch_resp_auth = estimate_proc_time_s(do_sign=True, do_tips=True)

            success_resp_auth = propagate_with_probability(per=per_resp_auth_ch_sink, override_per=PER_VARIABLE)
            p_lost_resp_auth = not success_resp_auth
            bits_sent_resp_auth = 1600 # bits
            bits_received_resp_auth = 1600 if success_resp_auth else 0

            # guardar la energía antes de actualizar
            initial_energy_ch_tx = ch_node1["ResidualEnergy"]
            # Calcular el timeout de espera
            lat_prop, lat_tx, _, timeout_ch_resp_auth = calculate_timeout(start_position, end_position, bitrate=9200, packet_size=1600)
            # Actualiza energía del nodo
            ch_node1 = update_energy_node_tdma(ch_node1, sink1["Position"], E_schedule,
                                                timeout_ch_resp_auth, type_packet, role='CH', action='tx', verbose=True, t_verif_s=t_proc_ch_resp_auth)
            energy_consumed_ch_tx = ((initial_energy_ch_tx - ch_node1["ResidualEnergy"]))
            print(f'Energy consumed del CH en Tx - Tx-genesis : ', energy_consumed_ch_tx)

            # Se almacena en log_event de la tx del ack:auth
            log_event(
                run_id=RUN_ID, phase="auth", module="tangle", msg_type="AUTH:RESP",
                sender_id=ch_node1["NodeID"], receiver_id=sink1["NodeID"], cluster_id=ch_node1["ClusterHead"],
                start_pos=start_position, end_pos=end_position,
                bits_sent=bits_sent_resp_auth, bits_received=bits_received_resp_auth,
                success=success_resp_auth, packet_lost=p_lost_resp_auth,
                energy_event_type='tx', energy_j=energy_consumed_ch_tx,
                residual_sender=ch_node1["ResidualEnergy"], residual_receiver=None,
                bitrate=9200, freq_khz=20,
                lat_prop_ms=lat_prop, lat_tx_ms=lat_tx, lat_proc_ms=t_proc_ch_resp_auth,
                snr_db=snr_db, per=per_resp_auth_ch_sink,
                lat_dag_ms=0.0, SL_db=SL_db, EbN0_db=EbN0_db, BER=ber
                )

            ## Energia de los demas nodos
            active_ids = [ch_node1["NodeID"]]
            node_uw3 = update_energy_standby_others(node_uw3, active_ids, timeout_ch_resp_auth, verbose=True)

            # # CH to Sink
            # print('####')
            # print('Antes de actualizar el CH imprimimos el esatdo del nodo : ', ch_node1)
            # print('####')

            # # Aqui se agrega la TX en el tips del nodo
            # ch_node1['Tips'].append(auth_response_tx1['ID'])

            # # Tambien se debe actualizar el propio nodo con la Tx que esta aprobando
            # update_transactions(ch_node1, auth_response_tx1)

            # print('####')
            # print('Despues de actualizar el CH imprimimos el esatdo del nodo : ', ch_node1)
            # print('####')

            # Simular la probabiidad de recepción AL SINK
            if success_resp_auth:
                ack_received_chtosink = True
                # El CH coloca su estado de autenticado cuando inicia el proceso de propagación de la TX
                ch_node1['Authenticated'] = True

                payload = auth_response_tx1['Payload']
                # Dividir el payload por el separador ";"
                payload_parts = payload.split(';') # obtener el identificador de la firma utilizada
                id_pair_keys_sign = payload_parts[1] # Obtener el identificador del par de firmas (segundo elemento)

                # Si la tx llega al nodo debe identificar la id de la clave utilizada para validar la firma
                _, key_public_sign = load_keys_sign_withou_cipher("bbdd_keys_shared_sign_cipher.db", "keys_sign_ed25519",
                                                                index=id_pair_keys_sign)

                # Verificar la Tx con la clave pública del Sink
                # calcular el tiempo de verificación tx por parte del CH
                time_start = time.perf_counter()
                isverify = verify_transaction_signature(auth_response_tx1, auth_response_tx1['Signature'], key_public_sign)
                end_time_verify = time.perf_counter() - time_start

                # guardar la energía antes de actualizar, recibir el ACK del sink
                initial_energy_ch_rx = ch_node1["ResidualEnergy"]
                # Calcular el timeout de espera
                lat_prop, lat_tx, lat_proc, timeout_ch = calculate_timeout(start_position, end_position, bitrate=9200, packet_size=48)
                # Actualiza energía del nodo
                ch_node1 = update_energy_node_tdma(ch_node1, sink1["Position"], E_schedule,
                                                   timeout_ch, type_packet_control, role='CH', action='rx', verbose=True)
                energy_consumed_ch_rx = ((initial_energy_ch_rx - ch_node1["ResidualEnergy"]))
                print(f'Energy consumed del CH en Tx - Tx-genesis : ', energy_consumed_ch_rx)

                 # Se almacena en log_event
                log_event(
                    run_id=RUN_ID, phase="auth", module="tangle", msg_type="AUTH:RESP",
                    sender_id=ch_node1["NodeID"], receiver_id=sink1["NodeID"], cluster_id=ch_node1["ClusterHead"],
                    start_pos=start_position, end_pos=end_position,
                    bits_sent=bits_sent_resp_auth, bits_received=bits_received_resp_auth,
                    success=success_resp_auth, packet_lost=p_lost_resp_auth,
                    energy_event_type='rx', energy_j=energy_consumed_ch_rx,
                    residual_sender=None, residual_receiver=ch_node1["ResidualEnergy"],
                    bitrate=9200, freq_khz=20,
                    lat_prop_ms=lat_prop, lat_tx_ms=lat_tx, lat_proc_ms=lat_proc,
                    snr_db=snr_db, per=per_resp_auth_ch_sink,
                    lat_dag_ms=0.0, SL_db=SL_db, EbN0_db=EbN0_db, BER=ber
                    )

                # # CH to Sink
                # La tx es verificada por el sink con la firma publica obtenida de la bbdd, el identificador
                # de la firma se envio en el payload
                if isverify:
                    print(f"El Sink recibió y verificó la Tx de Response_auth_to_sink de CH {ch_node1['NodeID']}")
                    sink1['Tips'].append(auth_response_tx1['ID'])

                    # Cuando hace la verificación de la Tx el sink puede indicar que el CH esta autenticado, en su registro
                    # Le restamos uno al Id_nodeCH porque accede por lista en ese orden.
                    sink1['RegisterNodes'][indexCH - 1]['Status_auth'] = True

                    print(f"Se actualizo información del nodo {ch_node1['NodeID']},  en el Sink {sink1['RegisterNodes'][indexCH - 1]['Status_auth']}")

                    # Actualizar las transacciones en el sink
                    update_transactions(sink1, auth_response_tx_sink)
                else:
                    print(f"El Sink falló en la verificación de la Tx de CH {ch_node1['NodeID']}")
            else:
                retries_ch += 1
                ack_received_chtosink = False
                # Actualiza la energía del nodo en caso de no recibir el pkt, pero esta escuchando en su slot
                ch_node1 = update_energy_failed_rx(ch_node1, sink1["Position"], timeout_ch, role="CH", verbose=False)

        if retries_ch == max_retries:
            print(f"Sink {sink1['NodeID']} no respondió tras {max_retries} reintentos.")


        # # Aqui se agrega la TX en el tips del nodo
        # ch_node1['Tips'].append(auth_response_tx1['ID'])

        # # Actualizar la tx de Tips a ApprovedTransactions del ch
        # update_transactions(ch_node1, auth_response_tx1)

        ack_received_chtosn = False
        ##
        ##
        # Propagar la respuesta del CH a los nodos del cluster
        # CH -> SN
        for node2 in node_uw3:
            retries_SNtoCH = retries_sn = 0
            ack_received_chtosn = False
            ack_received_sntoch = False
            if node2['ClusterHead'] == ch_node1['NodeID'] and node2['IsSynced'] and node2['NodeID'] != ch_node1['NodeID']:  # Excluir el propio CH

                while retries_sn < max_retries and not ack_received_chtosn:
                    start_response_tx_ch = time.perf_counter()

                    # Aqui toca agregar el delay de propagación basasdo en la formula de distancia/velocidad
                    # calcular la distancia entre los nodos
                    dist = np.linalg.norm(ch_node1["Position"] - node2["Position"]) # se debe comentar 10/09/2025

                    start_position = ch_node1["Position"]
                    end_position = node2["Position"]
                    # delay = propagation_time(dist, start_position, end_position)    # se comenta 10/09/2025

                    delay = propagation_time1(start_position, end_position, depth=None, region="standard")

                    print(f"CH {ch_node1['NodeID']} enviando Tx Response_auth_to_sink al nodo {node2['NodeID']} de su cluster, retraso de {delay:.2f} segundos, distancia calculada {dist:.2f}")
                    # time.sleep(delay)  # Simular el tiempo de sincronización

                    # times_propagation_tx_response = times_propagation_tx_response + (time.time() - start_response_tx_ch)
                    # times_propagation_tx_response = delay

                    per_resp_auth_ch_sn, SL_db, snr_db, EbN0_db, ber = per_from_link(f_khz=20, distance_m=dist, L=1600, bitrate=9200)
                    success_resp_auth = propagate_with_probability(per=per_resp_auth_ch_sn, override_per=PER_VARIABLE)
                    p_lost_resp_auth = not success_resp_auth
                    bits_sent_resp_auth = 1600 # bits
                    bits_received_resp_auth = 1600 if success_resp_auth else 0

                    # guardar la energía antes de actualizar
                    initial_energy_ch_tx = ch_node1["ResidualEnergy"]
                    # Calcular el timeout de espera
                    lat_prop, lat_tx, lat_proc, timeout_ch = calculate_timeout(start_position, end_position, bitrate=9200, packet_size=1600)
                    # Actualiza energía del nodo
                    ch_node1 = update_energy_node_tdma(ch_node1, node2["Position"], E_schedule,
                                                        timeout_ch, type_packet, role='CH', action='tx', verbose=True)
                    energy_consumed_ch_tx = ((initial_energy_ch_tx - ch_node1["ResidualEnergy"]))
                    print(f'Energy consumed del CH en Tx - Tx-response : ', energy_consumed_ch_tx)

                    # Se almacena en log_event de la tx del ack:auth
                    log_event(
                        run_id=RUN_ID, phase="auth", module="tangle", msg_type="AUTH:RESP",
                        sender_id=ch_node1["NodeID"], receiver_id=node2["NodeID"], cluster_id=node2["ClusterHead"],
                        start_pos=start_position, end_pos=end_position,
                        bits_sent=bits_sent_resp_auth, bits_received=bits_received_resp_auth,
                        success=success_resp_auth, packet_lost=p_lost_resp_auth,
                        energy_event_type='tx', energy_j=energy_consumed_ch_tx,
                        residual_sender=ch_node1["ResidualEnergy"], residual_receiver=node2["ResidualEnergy"],
                        bitrate=9200, freq_khz=20,
                        lat_prop_ms=lat_prop, lat_tx_ms=lat_tx, lat_proc_ms=lat_proc,
                        snr_db=snr_db, per=per_resp_auth_ch_sn,
                        lat_dag_ms=0.0, SL_db=SL_db, EbN0_db=EbN0_db, BER=ber
                        )

                    ## Energia de los demas nodos
                    active_ids = [ch_node1["NodeID"], node2["NodeID"]]
                    node_uw3 = update_energy_standby_others(node_uw3, active_ids, timeout_ch, verbose=True)

                    # # CH to SN
                    if success_resp_auth:
                        ack_received_chtosn = True
                        # Los nodos que reciben la Tx de respuesta del CH, tambien deben buscar la clave en la bbd y verificarl
                        # print(f"El nodo sensor {node['NodeID']} recibio la Tx del CH {ch['NodeID']}...")

                        payload = auth_response_tx1['Payload']
                        # Dividir el payload por el separador ";"
                        payload_parts = payload.split(';') # obtener el identificador de la firma utilizada
                        id_pair_keys_sign = payload_parts[1] # Obtener el identificador del par de firmas (segundo elemento)

                        # Si la tx llega al nodo debe identificar la id de la clave utilizada para validar la firma
                        _, key_public_sign = load_keys_sign_withou_cipher("bbdd_keys_shared_sign_cipher.db", "keys_sign_ed25519", index=id_pair_keys_sign)

                        # Verificar la Tx con la clave pública del Sink
                        # calcular el tiempo de verificación tx por parte del CH
                        time_start1 = time.perf_counter()
                        isverify2 = verify_transaction_signature(auth_response_tx1, auth_response_tx1['Signature'], key_public_sign)
                        end_time_verify1 = time.perf_counter() - time_start1

                        # SN recibe y verifica la tx del ch
                        t_proc_ch_resp_auth = estimate_proc_time_s(do_verify=True, do_tips=True)

                        # guardar la energía antes de actualizar
                        initial_energy_sn_rx = node2["ResidualEnergy"]
                        # Calcular el timeout de espera
                        lat_prop, lat_tx, lat_proc, timeout_sn = calculate_timeout(start_position, end_position, bitrate=9200, packet_size=1600)
                        # Actualiza energía del nodo
                        node2 = update_energy_node_tdma(node2, ch_node1["Position"], E_schedule,
                                                            timeout_sn, type_packet, role='SN', action='rx', verbose=True, t_verif_s=t_proc_ch_resp_auth)
                        energy_consumed_sn_rx = ((initial_energy_sn_rx - node2["ResidualEnergy"]))
                        print(f'Energy consumed del CH en Tx - Tx-response : ', energy_consumed_sn_rx)

                        # Se almacena en log_event de la tx del ack:auth
                        log_event(
                            run_id=RUN_ID, phase="auth", module="tangle", msg_type="AUTH:RESP",
                            sender_id=ch_node1["NodeID"], receiver_id=node2["NodeID"], cluster_id=node2["ClusterHead"],
                            start_pos=start_position, end_pos=end_position,
                            bits_sent=bits_sent_resp_auth, bits_received=bits_received_resp_auth,
                            success=success_resp_auth, packet_lost=p_lost_resp_auth,
                            energy_event_type='rx', energy_j=energy_consumed_sn_rx,
                            residual_sender=ch_node1["ResidualEnergy"], residual_receiver=node2["ResidualEnergy"],
                            bitrate=9200, freq_khz=20,
                            lat_prop_ms=lat_prop, lat_tx_ms=lat_tx, lat_proc_ms=t_proc_ch_resp_auth,
                            snr_db=snr_db, per=per_resp_auth_ch_sn,
                            lat_dag_ms=0.0, SL_db=SL_db, EbN0_db=EbN0_db, BER=ber
                            )

                        # # CH to SN
                        if isverify2:
                            print(f"Nodo {node2['NodeID']} recibió y verifico la Tx Response_auth_to_sink de CH {ch_node1['NodeID']}")

                            # Se actualiza el ID del tip en el nodo
                            node2['Tips'].append(auth_response_tx1['ID']) # corregido

                            # break
                            while retries_SNtoCH < max_retries and not ack_received_sntoch:
                                # calular el per
                                per_sn_resp_ack, SL_db, snr_db, EbN0_db, ber = per_from_link(f_khz=20, distance_m=dist, L=48, bitrate=9200)
                                success_resp_ack = propagate_with_probability(per=per_sn_resp_ack, override_per=PER_VARIABLE)
                                p_lost_resp_ack = not success_resp_ack
                                bits_sent_resp_ack = 48 # bits
                                bits_received_resp_ack = 48 if success_resp_ack else 0

                                # guardar la energía antes de actualizar
                                initial_energy_sn_tx = node2["ResidualEnergy"]
                                # Calcular el timeout de espera
                                lat_prop, lat_tx, lat_proc, timeout_sn = calculate_timeout(start_position, end_position, bitrate=9200, packet_size=48)
                                # Actualiza energía del nodo
                                node2 = update_energy_node_tdma(node2, ch_node1["Position"], E_schedule,
                                                                    timeout_sn, type_packet_control, role='SN', action='tx', verbose=True)
                                energy_consumed_sn_tx = ((initial_energy_sn_tx - node2["ResidualEnergy"]))

                                ## Energia de los demas nodos
                                active_ids = [ch_node1["NodeID"], node2["NodeID"]]
                                node_uw3 = update_energy_standby_others(node_uw3, active_ids, t_proc_ch_resp_auth, verbose=True)

                                # Se almacena en log_event de la tx del ack:auth
                                log_event(
                                    run_id=RUN_ID, phase="auth", module="tangle", msg_type="AUTH:RESP:ACK",
                                    sender_id=node2["NodeID"], receiver_id=ch_node1["NodeID"], cluster_id=node2["ClusterHead"],
                                    start_pos=start_position, end_pos=end_position,
                                    bits_sent=bits_sent_resp_ack, bits_received=bits_received_resp_ack,
                                    success=success_resp_ack, packet_lost=p_lost_resp_ack,
                                    energy_event_type='tx', energy_j=energy_consumed_sn_tx,
                                    residual_sender=node2["ResidualEnergy"], residual_receiver=ch_node1["ResidualEnergy"],
                                    bitrate=9200, freq_khz=20,
                                    lat_prop_ms=lat_prop, lat_tx_ms=lat_tx, lat_proc_ms=lat_proc,
                                    snr_db=snr_db, per=per_sn_resp_ack,
                                    lat_dag_ms=0.0, SL_db=SL_db, EbN0_db=EbN0_db, BER=ber
                                    )

                                if success_resp_ack:
                                    ack_received_sntoch = True
                                    # guardar la energía antes de actualizar
                                    initial_energy_ch_rx = ch_node1["ResidualEnergy"]
                                    # Calcular el timeout de espera
                                    lat_prop, lat_tx, lat_proc, timeout_ch = calculate_timeout(start_position, end_position, bitrate=9200, packet_size=48)
                                    # Actualiza energía del nodo
                                    ch_node1 = update_energy_node_tdma(ch_node1, node2["Position"], E_schedule,
                                                                        timeout_ch, type_packet_control, role='CH', action='rx', verbose=True)
                                    energy_consumed_ch_rx = ((initial_energy_ch_rx - ch_node1["ResidualEnergy"]))

                                    # Se almacena en log_event de la tx del ack:auth
                                    log_event(
                                        run_id=RUN_ID, phase="auth", module="tangle", msg_type="AUTH:RESP:ACK",
                                        sender_id=node2["NodeID"], receiver_id=ch_node1["NodeID"], cluster_id=node2["ClusterHead"],
                                        start_pos=start_position, end_pos=end_position,
                                        bits_sent=bits_sent_resp_ack, bits_received=bits_received_resp_ack,
                                        success=success_resp_ack, packet_lost=p_lost_resp_ack,
                                        energy_event_type='rx', energy_j=energy_consumed_ch_rx,
                                        residual_sender=node2["ResidualEnergy"], residual_receiver=ch_node1["ResidualEnergy"],
                                        bitrate=9200, freq_khz=20,
                                        lat_prop_ms=lat_prop, lat_tx_ms=lat_tx, lat_proc_ms=lat_proc,
                                        snr_db=snr_db, per=per_sn_resp_ack,
                                        lat_dag_ms=0.0, SL_db=SL_db, EbN0_db=EbN0_db, BER=ber
                                        )
                                else:
                                    # En caso de que el sn no reciba el ack de confirmación
                                    ack_received_sntoch = False
                                    retries_SNtoCH += 1
                                    # Actualiza la energía del nodo en caso de no recibir el pkt, pero esta escuchando en su slot
                                    ch_node1 = update_energy_failed_rx(ch_node1, node2["Position"], timeout_sn, role="CH", verbose=False)
                        else:
                            print(f"Nodo {node2['NodeID']} falló en la verificación de la Tx de autenticación.")
                            # retries += 1
                            # time.sleep(timeout)
                    else:
                        retries_sn += 1
                        print(f"Nodo {node2['NodeID']} no recibió la Tx de autenticación. Reintentando... ({retries_sn}/{max_retries})")
                        # Actualiza la energía del nodo en caso de no recibir el pkt, pero esta escuchando en su slot
                        node2 = update_energy_failed_rx(node2, ch_node1["Position"], timeout_sn, role="SN", verbose=False)
                        # time.sleep(timeout)

                if retries_sn == max_retries:
                    print(f"Nodo {node2['NodeID']} no respondió tras {max_retries} reintentos.")

    return # times_response_all_ch, times_propagation_tx_response

# Filtrado de Nodos Sincronizados: Primero se filtran los nodos que deben autenticarse con el CH, asegurando que sean nodos sincronizados y que no sean el propio CH.
# Generación de la Transacción: Los nodos generan una transacción de autenticación que envían al CH.
# Verificación del CH: El CH verifica si el nodo está sincronizado y procede a validar la firma con la clave pública obtenida de la base de datos.
# Actualización del Estado del CH: Si la autenticación es exitosa, el CH registra la autenticación del nodo. Si no, el proceso puede reintentarse hasta alcanzar el máximo de intentos.

# Función para propagar la tx de respuesta de los nodos de cada cluster
# SN -> CH
def authenticate_nodes_to_ch(RUN_ID, nodes, chead, E_schedule, ronda, max_retries=3, timeout=2):
    """
    Función para que los nodos del clúster generen una Tx de autenticación y la envíen al CH.
    nodes: Diccionario con los nodos de la red.
    chead: Nodo CH que recibe las transacciones de autenticación.
    max_retries: Número máximo de reintentos.
    timeout: Tiempo de espera entre reintentos.
    """
    print('El ch que se pasa : ', chead)
    CONTADOR_EVENTOS = 0
    initial_energy_sn_rx = initial_energy_sn_tx = 0
    initial_energy_ch_rx = initial_energy_ch_tx = 0

    type_packet = "tx"
    type_packet_control = "sync"

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
            retries = retries_sntoch = 0
            authenticated = False
            authenticated_ack = False

            # Response_auth_to_CH
            time_start_responseSN = time.perf_counter() # Incia tiempo de medición de la creación de la nueva Tx de response
            # Crear transacción de autenticación para el CH
            node_auth_tx = create_auth_response_tx(node4)
            end_time_responseSN = time.perf_counter() - time_start_responseSN

            # Agregar la tx como tips en el nodo, se agrega aqui despues de todo el proceso
            node4['Tips'].append(node_auth_tx['ID'])    # corregido

            while retries < max_retries and not authenticated:

                print(f"Nodo {node4['NodeID']} intenta autenticarse con el CH {node_ch['NodeID']}...")

                # Aqui toca agregar el delay de propagación basasdo en la formula de distancia/velocidad
                # delay = random_sync_delay()  # Generar un tiempo de retraso aleatorio
                # calcular la distancia entre los nodos
                dist = np.linalg.norm(node_ch["Position"] - node4["Position"])  # se debe comentar 10/09/2025

                start_position = node4["Position"]
                end_position = node_ch["Position"]
                # delay = propagation_time(dist, start_position, end_position)    # se comenta 10/09/2025
                delay = propagation_time1(start_position, end_position, depth=None, region="standard")

                print(f"Nodo {node4['NodeID']} envia Tx Response_auth_to_ch al CH {node_ch['NodeID']}, retraso de {delay:.2f} segundos, distancia calculada {dist:.2f}")
                # time.sleep(delay)  # Simular el tiempo de sincronización

                per_sn_resp_ch, SL_db, snr_db, EbN0_db, ber = per_from_link(f_khz=20, distance_m=dist, L=1600, bitrate=9200)
                # SN crea y firma tx de respuesta al CH
                t_proc_sn_resp_auth = estimate_proc_time_s(do_sign=True, do_tips=True)

                success_resp_auth = propagate_with_probability(per=per_sn_resp_ch, override_per=PER_VARIABLE)
                p_lost_resp_auth = not success_resp_auth
                bits_sent_resp_auth = 1600 # bits
                bits_received_resp_auth = 1600 if success_resp_auth else 0

                # guardar la energía antes de actualizar
                initial_energy_sn_tx = node4["ResidualEnergy"]
                # Calcular el timeout de espera
                lat_prop, lat_tx, lat_proc, timeout_sn = calculate_timeout(start_position, end_position, bitrate=9200, packet_size=1600)
                # Actualiza energía del nodo
                node4 = update_energy_node_tdma(node4, node_ch["Position"], E_schedule,
                                                            timeout_sn, type_packet, role='SN', action='tx', verbose=True, t_verif_s=t_proc_sn_resp_auth)
                energy_consumed_sn_tx = ((initial_energy_sn_tx - node4["ResidualEnergy"]))
                print(f'Energy consumed del SN en Tx - Tx-responseSN : ', energy_consumed_sn_tx)

                # Se almacena en log_event de la tx del ack:auth
                log_event(
                    run_id=RUN_ID, phase="auth", module="tangle", msg_type="AUTH:RESP",
                    sender_id=node4["NodeID"], receiver_id=node_ch["NodeID"], cluster_id=node4["ClusterHead"],
                    start_pos=start_position, end_pos=end_position,
                    bits_sent=bits_sent_resp_auth, bits_received=bits_received_resp_auth,
                    success=success_resp_auth, packet_lost=p_lost_resp_auth,
                    energy_event_type='tx', energy_j=energy_consumed_sn_tx,
                    residual_sender=node4["ResidualEnergy"], residual_receiver=node_ch["ResidualEnergy"],
                    bitrate=9200, freq_khz=20,
                    lat_prop_ms=lat_prop, lat_tx_ms=lat_tx, lat_proc_ms=t_proc_sn_resp_auth,
                    snr_db=snr_db, per=per_sn_resp_ch,
                    lat_dag_ms=0.0, SL_db=SL_db, EbN0_db=EbN0_db, BER=ber
                    )

                ## Energia de los demas nodos
                active_ids = [node_ch["NodeID"], node4["NodeID"]]
                nodes = update_energy_standby_others(nodes, active_ids, timeout_sn, verbose=True)
                
                if success_resp_auth:
                    # CH recibe la transacción y verifica si el nodo está sincronizado
                    if node4['IsSynced']:
                        # Dividir el payload para obtener el identificador de la firma
                        payload = node_auth_tx['Payload']
                        payload_parts = payload.split(';')
                        id_pair_keys_sign = payload_parts[1]

                        # Cargar la clave pública desde la base de datos usando el identificador
                        _, key_public_sign = load_keys_sign_withou_cipher("bbdd_keys_shared_sign_cipher.db", "keys_sign_ed25519", index=id_pair_keys_sign)

                        # Verificar la Tx con la clave pública del Sink
                        # calcular el tiempo de verificación tx por parte del CH
                        time_start1 = time.perf_counter()
                        isverify2 = verify_transaction_signature(node_auth_tx, node_auth_tx['Signature'], key_public_sign)
                        end_time_verify1 = time.perf_counter() - time_start1

                        # guardar la energía antes de actualizar
                        initial_energy_ch_rx = node_ch["ResidualEnergy"]
                        # Calcular el timeout de espera
                        lat_prop, lat_tx, lat_proc, timeout_ch = calculate_timeout(start_position, end_position, bitrate=9200, packet_size=1600)
                        # Actualiza energía del nodo
                        node_ch = update_energy_node_tdma(node_ch, node4["Position"], E_schedule,
                                                            timeout_ch, type_packet, role='CH', action='rx', verbose=True)
                        energy_consumed_ch_rx = ((initial_energy_ch_rx - node_ch["ResidualEnergy"]))
                        print(f'Energy consumed del CH en Rx - Tx-responseSN : ', energy_consumed_ch_rx)

                        # Se almacena en log_event de la tx del ack:auth
                        log_event(
                            run_id=RUN_ID, phase="auth", module="tangle", msg_type="AUTH:RESP",
                            sender_id=node4["NodeID"], receiver_id=node_ch["NodeID"], cluster_id=node4["ClusterHead"],
                            start_pos=start_position, end_pos=end_position,
                            bits_sent=bits_sent_resp_auth, bits_received=bits_received_resp_auth,
                            success=success_resp_auth, packet_lost=p_lost_resp_auth,
                            energy_event_type='rx', energy_j=energy_consumed_ch_rx,
                            residual_sender=node4["ResidualEnergy"], residual_receiver=node_ch["ResidualEnergy"],
                            bitrate=9200, freq_khz=20,
                            lat_prop_ms=lat_prop, lat_tx_ms=lat_tx, lat_proc_ms=lat_proc,
                            snr_db=snr_db, per=per_sn_resp_ch,
                            lat_dag_ms=0.0, SL_db=SL_db, EbN0_db=EbN0_db, BER=ber
                            )

                        # CH to SN
                        # Verificar la transacción con la clave pública
                        if isverify2:
                            print(f"CH {node_ch['NodeID']} recibió y verificó la Tx Response_auth_to_ch del Nodo {node4['NodeID']}.")
                            node4['Authenticated'] = True  # Se autentica exitosamente
                            authenticated = True

                            # Se agrega el id de tx al ch
                            node_ch['Tips'].append(node_auth_tx['ID'])  # corregido

                            # Actualizar el nodo dentro del cluster
                            update_transactions(node4, node_auth_tx)    # corregido

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

                            ## while
                            while retries_sntoch < max_retries and not authenticated_ack:
                                # confirma la Rx con ACK
                                # guardar la energía antes de actualizar
                                per_sn_resp_ack_ch, SL_db, snr_db, EbN0_db, ber = per_from_link(f_khz=20, distance_m=dist, L=48, bitrate=9200)

                                # CH confirma el ack
                                success_resp_auth_ack = propagate_with_probability(per=per_sn_resp_ack_ch, override_per=PER_VARIABLE)
                                p_lost_resp_auth_ack = not success_resp_auth_ack
                                bits_sent_resp_auth_ack = 48 # bits
                                bits_received_resp_auth_ack = 48 if success_resp_auth else 0

                                # Calcular el timeout de espera
                                lat_prop, lat_tx, lat_proc, timeout_ch = calculate_timeout(start_position, end_position, bitrate=9200, packet_size=48)

                                initial_energy_ch_tx = node_ch["ResidualEnergy"]
                                # Actualiza energía del nodo
                                node_ch = update_energy_node_tdma(node_ch, node4["Position"], E_schedule,
                                                                    timeout_ch, type_packet_control, role='CH', action='tx', verbose=True)
                                energy_consumed_ch_tx = ((initial_energy_ch_tx - node_ch["ResidualEnergy"]))
                                print(f'Energy consumed del CH en Tx - Tx-response-ACK : ', energy_consumed_ch_tx)

                                # Se almacena en log_event de la tx del ack:auth
                                log_event(
                                    run_id=RUN_ID, phase="auth", module="tangle", msg_type="AUTH:RESP:ACK",
                                    sender_id=node_ch["NodeID"], receiver_id=node4["NodeID"], cluster_id=node4["ClusterHead"],
                                    start_pos=start_position, end_pos=end_position,
                                    bits_sent=bits_sent_resp_auth_ack, bits_received=bits_received_resp_auth_ack,
                                    success=success_resp_auth_ack, packet_lost=p_lost_resp_auth_ack,
                                    energy_event_type='tx', energy_j=energy_consumed_ch_tx,
                                    residual_sender=node_ch["ResidualEnergy"], residual_receiver=node4["ResidualEnergy"],
                                    bitrate=9200, freq_khz=20,
                                    lat_prop_ms=lat_prop, lat_tx_ms=lat_tx, lat_proc_ms=lat_proc,
                                    snr_db=snr_db, per=per_sn_resp_ch,
                                    lat_dag_ms=0.0, SL_db=SL_db, EbN0_db=EbN0_db, BER=ber
                                    )

                                ## Energia de los demas nodos
                                active_ids = [node_ch["NodeID"], node4["NodeID"]]
                                nodes = update_energy_standby_others(nodes, active_ids, timeout_ch, verbose=True)

                                if success_resp_auth_ack:
                                    authenticated_ack = True
                                    # Recepción del ACK del CH
                                    # guardar la energía antes de actualizar
                                    initial_energy_sn_rx = node4["ResidualEnergy"]
                                    # Calcular el timeout de espera
                                    lat_prop, lat_tx, lat_proc, timeout_sn = calculate_timeout(start_position, end_position, bitrate=9200, packet_size=48)
                                    # Actualiza energía del nodo
                                    node4 = update_energy_node_tdma(node4, node_ch["Position"], E_schedule,
                                                                                timeout_sn, type_packet_control, role='SN', action='rx', verbose=True)
                                    energy_consumed_sn_rx = ((initial_energy_sn_rx - node4["ResidualEnergy"]))
                                    print(f'Energy consumed del SN en Tx - Tx-responseSN : ', energy_consumed_sn_rx)

                                    # Se almacena en log_event de la tx del ack:auth
                                    log_event(
                                        run_id=RUN_ID, phase="auth", module="tangle", msg_type="AUTH:RESP:ACK",
                                        sender_id=node_ch["NodeID"], receiver_id=node4["NodeID"], cluster_id=node4["ClusterHead"],
                                        start_pos=start_position, end_pos=end_position,
                                        bits_sent=bits_sent_resp_auth_ack, bits_received=bits_received_resp_auth_ack,
                                        success=success_resp_auth_ack, packet_lost=p_lost_resp_auth_ack,
                                        energy_event_type='rx', energy_j=energy_consumed_sn_rx,
                                        residual_sender=node_ch["ResidualEnergy"], residual_receiver=node4["ResidualEnergy"],
                                        bitrate=9200, freq_khz=20,
                                        lat_prop_ms=lat_prop, lat_tx_ms=lat_tx, lat_proc_ms=lat_proc,
                                        snr_db=snr_db, per=per_sn_resp_ch,
                                        lat_dag_ms=0.0, SL_db=SL_db, EbN0_db=EbN0_db, BER=ber
                                        )
                                else:
                                    ## en caso del que nodo SN no reciba el ack del CH
                                    authenticated_ack = False
                                    retries_sntoch += 1
                                    # Actualiza la energía del nodo en caso de no recibir el pkt, pero esta escuchando en su slot
                                    node4 = update_energy_failed_rx(node4, node_ch["Position"], timeout_sn, role="SN", verbose=False)
                        else:
                            print(f"CH {node_ch['NodeID']} falló en la verificación de la autenticación de Nodo {node4['NodeID']}.")
                            # retries += 1
                            # time.sleep(timeout)
                    else:
                        print(f"El Nodo {node4['NodeID']} no está sincronizado con el CH {node_ch['NodeID']}. No se puede autenticar.")
                else:
                    retries += 1
                    print(f"CH {node_ch['NodeID']} no recibió la Tx de autenticación. Reintentando... ({retries}/{max_retries})")
                    # Actualiza la energía del nodo en caso de no recibir el pkt, pero esta escuchando en su slot
                    node_ch = update_energy_failed_rx(node_ch, node4["Position"], timeout_ch, role="CH", verbose=False)
                    # time.sleep(timeout)

            if retries == max_retries:
                print(f"CH {node_ch['NodeID']} no autenticó al Nodo {node4['NodeID']} tras {max_retries} reintentos.")
    return


# Nueva función de update_transactions
import copy

def update_transactions(node, received_transaction):
    """
    Actualiza la lista de transacciones del nodo, moviendo Tips a ApprovedTransactions.
    Además, trabaja con una copia de la transacción recibida para evitar modificar la original.
    node: Diccionario del nodo.
    received_transaction: Transacción recibida que contiene detalles de aprobaciones.
    """
    # print('Nodo que se va a actualizar : ', node["NodeID"])

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
    # print('Nodo actualizado en ApprovedTransactions:', node["ApprovedTransactions"])
    # print('Tips restantes:', node["Tips"])



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



# Registrar eventos
def registrar_evento_tabla(tabla, id_evento, tipo, origen, destino, rol_origen, rol_destino,
                           energia_tx=None, energia_rx=None, t_prop=None, t_verif=None, t_auth=None,
                           t_resp=None, clusterID=None, RoundID=None):
    tabla.append({
        "ID_evento": id_evento,
        "Tipo": tipo,
        "Origen": origen,
        "Destino": destino,
        "Rol_Origen": rol_origen,
        "Rol_Destino": rol_destino,
        "Energia_Tx": energia_tx,
        "Energia_Rx": energia_rx,
        "T_Propagaciin": t_prop,
        "T_Verificaciin": t_verif,
        "T_Auth": t_auth,
        "T_Respuesta": t_resp,
        "ClusterID": clusterID,  # o node_dest si es CH
        "RoundID": RoundID  # si haces múltiples rondas
    })
