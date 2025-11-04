import time
import numpy as np
from path_loss import compute_path_loss, propagation_time1
from energia_dinamica import (calcular_energia_paquete, energy_listen, energy_standby, calculate_timeout, 
                              update_energy_node_tdma, update_energy_standby_others, update_energy_failed_rx, estimate_proc_time_s)
from transmission_logger_uan import log_event
from per_from_link_uan import per_from_link, propagate_with_probability

global VERBOSE

PER_VARIABLE = None
VERBOSE = False
PACKET_SIZE_SYN = 72 # bits
PAYLOAD_ACK = 0 # bits

# Función para crear un paquete SYN desde el Sink
def create_syn_packet(sink_id):
    packet = {
        "PacketID": np.random.randint(0, 65535),    # 2B - ID del paquete 
        "PacketType": b'0x10',                      # 2B - Tipo de paquete SYN
        "SourceID": sink_id,                        # 2B - ID del Sink
        "Timestamp": time.time(),                   # 4B - Marca de tiempo actual
        #"Hops": 0                                  # Inicialmente 0 saltos
    }
    return packet

# Función para agregar a los CHs si los nodos se sincronizan o no
def register_node_to_ch(ch_id, node_id, is_synced, is_authenticated, node_uw):
    # Crear la estructura para el nodo
    node_info = {
        "NodeID": node_id,
        "Status_syn": is_synced,
         "Status_auth": is_authenticated
    }
    # Agregar al registro del CH
    node_uw[ch_id]["RegisterNodes"].append(node_info)

# IMPLEMENTADO TDMA

# Función para propagar el paquete SYN y actualizar la energía de los nodos
def propagate_syn_to_CH_tdma(RUN_ID, sink, CH_ids, node_uw, max_retries=3, timeout=2, E_schedule=5e-9):
    
    # timestamp = time.time()  # Marca de tiempo actual en segundos
    timeout_sinktoch = timeout

    # Genera el paquete el Sink de sincronización
    syn_packet = create_syn_packet(sink["NodeID"])

    # Numero de intentos de envio
    max_retries_sensor = max_retries

    type_packet = "sync"

    # Intentar sincronizar cada CH
    for ch in CH_ids:
        retries_sinktoch = 0
        ack_received_CH = False
        ack_received_Sink = False

        initial_energy_tx = initial_energy_rx = 0
        energy_consumed_ch_tx = energy_consumed_ch_rx = 0  # Para capturar la energía consumida por el CH

        while retries_sinktoch < max_retries and not ack_received_CH:
            print(f"Enviando paquete SYN del Sink {sink['NodeID']} al Cluster Head {ch + 1} (Intento {retries_sinktoch+1})")
            # syn_packet["Hops"] += 1  # Aumentar el contador de saltos

            # Aqui toca agregar el delay de propagación basasdo en la formula de distancia/velocidad

            # delay = random_sync_delay()  # Generar un tiempo de retraso aleatorio
            # calcular la distancia entre los nodos
            dist = np.linalg.norm(node_uw[ch]["Position"] - sink["Position"])   # Se debe comentar 10/09/2025

            start_position = sink["Position"]
            end_position = node_uw[ch]["Position"]
            # delay = propagation_time(dist, start_position, end_position)    # se comenta 10/09/2025

            delay = propagation_time1(start_position, end_position, depth=None, region="standard")

            print(f"Sincronizando el CH {node_uw[ch]['NodeID']} bajo el Cluster Head Sink con un retraso de {delay:.2f} segundos, distancia calculada {dist:.2f}")
            
            # time.sleep(delay)  # Simular el tiempo de sincronización
            # Calcular el timeout de espera, se calcula el tiempo de procesamiento empirico 0.01 - 0.05 s
            lat_prop, lat_tx, lat_proc, timeout_sinktoch = calculate_timeout(start_position, end_position, bitrate=9200, packet_size=PACKET_SIZE_SYN)
            
            # calular el per
            per_sink_ch, SL_db, snr_db, EbN0_db, ber = per_from_link(f_khz=20, distance_m=dist, L=PACKET_SIZE_SYN, bitrate=9200)
            success_syn = propagate_with_probability(per=per_sink_ch, override_per=PER_VARIABLE)
            p_lost_syn = not success_syn
            bits_received_syn = PACKET_SIZE_SYN if success_syn else 0

            # DEscuenta energía de los demas nodos
            # Los nodos consumen cuando no estan transmitiendo.
            active_ids = [node_uw[ch]["NodeID"]]
            active_cluster_id = node_uw[ch]["ClusterHead"]
            node_uw = update_energy_standby_others(node_uw, active_ids, active_cluster_id, timeout_sinktoch, verbose=VERBOSE)

            # Simular probabilidad de recepción
            if success_syn: # Si recibe el packet de syn
                print("El paquete de syn se entrego al CH...")
                ack_received_CH = True  # confirmado

                # **Nuevo: Medir energía inicial del CH**
                initial_energy_rx = node_uw[ch]["ResidualEnergy"]

                # Actualizar la energía del Cluster Head
                node_uw[ch] = update_energy_node_tdma(node_uw[ch], sink["Position"], E_schedule, timeout_sinktoch, 
                                                      type_packet, role='CH', action='rx', verbose=VERBOSE)
                
                # **Nuevo: Calcular la energía consumida**
                energy_consumed_ch_rx = ((initial_energy_rx - node_uw[ch]["ResidualEnergy"]))

                # Registra el evento si recibe o no el paquete
                log_event(
                    run_id=RUN_ID, phase="sync", module="syn_light", msg_type="SYN:TDMA",
                    sender_id=sink["NodeID"], receiver_id=node_uw[ch]["NodeID"], cluster_id=node_uw[ch]["ClusterHead"],
                    start_pos=start_position, end_pos=end_position,
                    bits_sent=PACKET_SIZE_SYN, bits_received=bits_received_syn, payload_bits=PAYLOAD_ACK,
                    success=success_syn, packet_lost=p_lost_syn, 
                    energy_event_type='rx', energy_j=energy_consumed_ch_rx,
                    residual_sender=None, residual_receiver=node_uw[ch]["ResidualEnergy"],
                    bitrate=9200, freq_khz=20,
                    lat_prop_ms=lat_prop, lat_tx_ms=lat_tx, lat_proc_ms=lat_proc,
                    snr_db=snr_db, per=per_sink_ch,
                    lat_dag_ms=0.0, SL_db=SL_db, EbN0_db=EbN0_db, BER=ber
                    )
                
                retries_ChtoSink = 0

                while retries_ChtoSink < max_retries_sensor and not ack_received_Sink:
                    # **Nuevo: Medir energía inicial del CH**
                    initial_energy_tx = node_uw[ch]["ResidualEnergy"]

                    # calular el per
                    per_ack_ch_sink, SL_db, snr_db, EbN0_db, ber = per_from_link(f_khz=20, distance_m=dist, L=PACKET_SIZE_SYN, bitrate=9200)                
                    success_ack = propagate_with_probability(per=per_ack_ch_sink, override_per=PER_VARIABLE)
                    p_lost_ack = not success_ack
                    bits_received_ack = PACKET_SIZE_SYN if success_ack else 0
                    
                    # Actualiza energía de la tx de la confirmación (ACK)
                    node_uw[ch] = update_energy_node_tdma(node_uw[ch], sink["Position"], E_schedule, timeout_sinktoch, 
                                                          type_packet, role='CH', action='tx', verbose=VERBOSE)
                    # Estadistica

                    # **Nuevo: Calcular la energía consumida**
                    energy_consumed_ch_tx = ((initial_energy_tx - node_uw[ch]["ResidualEnergy"]))

                    # Registra el evento del ack
                    log_event(
                            run_id=RUN_ID, phase="sync", module="syn_light", msg_type="SYN:TDMA:ACK",
                            sender_id=node_uw[ch]["NodeID"], receiver_id=sink["NodeID"], cluster_id=node_uw[ch]["ClusterHead"],
                            start_pos=start_position, end_pos=end_position,
                            bits_sent=PACKET_SIZE_SYN, bits_received=bits_received_ack,
                            success=success_ack, packet_lost=p_lost_ack, 
                            energy_event_type='tx', energy_j=energy_consumed_ch_tx,
                            residual_sender=node_uw[ch]["ResidualEnergy"], residual_receiver=None,
                            bitrate=9200, freq_khz=20,
                            lat_prop_ms=lat_prop, lat_tx_ms=lat_tx, lat_proc_ms=lat_proc,
                            snr_db=snr_db, per=per_ack_ch_sink,
                            lat_dag_ms=0.0, SL_db=SL_db, EbN0_db=EbN0_db, BER=ber
                        )
                    
                    # Los nodos consumen cuando no estan transmitiendo.
                    active_ids = [node_uw[ch]["NodeID"]]
                    active_cluster_id = node_uw[ch]["ClusterHead"]
                    node_uw = update_energy_standby_others(node_uw, active_ids, active_cluster_id, timeout_sinktoch, verbose=VERBOSE)

                    # Simulación de recepción de ACK para el CH, se considera 0 como escenario ideal
                    # Pero se puede manejar una probabilidad de acuerdo a otros estudios
                    # En este caso no van a existir retransmisisones
                    # ack_received_CH = np.random.rand() > 0

                    if not success_ack:
                        print(f"Cluster Head {ch + 1} no envió ACK, posible retransmisión necesaria.")
                        retries_ChtoSink += 1
                        # time.sleep(timeout)  # Esperar antes de retransmitir (simulando backoff)
                    else:
                        ack_received_Sink = True               
                        print(f"Cluster Head {ch + 1} sincronizado exitosamente.")
                        node_uw[ch]["IsSynced"] = True  # Marcar el nodo como sincronizado
                        
                        # Si el CH se sincroniza exitosamente el Sink lo habilita como sincronizado
                        sink['RegisterNodes'][ch]['Status_syn'] = True

                    # Sincronizar nodos bajo el CH, auqnue el ack de respuesta no se haya recibido por el sink
                    synchronize_nodes_tdma(RUN_ID, ch, syn_packet, node_uw, max_retries_sensor, timeout_sinktoch, 
                                           type_packet, E_schedule)
                    success_syn = False
                    # # Los nodos consumen cuando no estan transmitiendo.
                    # active_ids = [node_uw[ch]["NodeID"]]
                    # node_uw = update_energy_standby_others(node_uw, active_ids, timeout_sinktoch, verbose=True)
            else:
                print("No se entrego el paquete de syn al CH...reintentando...")
                success_syn = False
                retries_sinktoch += 1
                # Actualiza la energía del nodo en caso de no recibir el pkt, pero esta escuchando en su slot
                node_uw[ch] = update_energy_failed_rx(node_uw[ch], sink["Position"], timeout_sinktoch, 
                                                      role="CH", verbose=VERBOSE)

        # if not node_uw[ch]["IsSynced"] and retries == max_retries:
        #     print(f"Fallo la sincronización con el Cluster Head {ch + 1} después de {retries} intentos.")
    return #syn_packet


# Función para sincronizar nodos con el Cluster Head, incluyendo retransmisiones en nodos sensores
def synchronize_nodes_tdma(RUN_ID, CH_id, syn_packet, node_uw, max_retries_sensor, timeout_sinktoch, type_packet, E_schedule):
    # print(f"Sincronizando Cluster Head {CH_id + 1} con Timestamp: {syn_packet['Timestamp']} y Hops: {syn_packet['Hops']}")
    print(f"Sincronizando Cluster Head {CH_id + 1} con Timestamp: {syn_packet['Timestamp']}")
    timeout_chtosn = 0
    # print(' Verificar CH_id en nodes : ', CH_id)

    # Filtrar los nodos que tienen a este CH como su ClusterHead y que no sean el propio CH
    cluster_nodes = [node for node in node_uw if node["ClusterHead"] == (CH_id + 1) and node["NodeID"] != (CH_id + 1)]
    # ack_received_node = False

    # Si ACK es recibido, propagar la sincronización a los nodos del clúster
    for node in cluster_nodes:
        retries_ChtoSn = 0
        ack_retries = 0
        ack_received_node = False
        ack_received_CH = False
        energy_consumed_ch_tx = energy_consumed_ch_rx = 0
        energy_consumed_sn_tx = energy_consumed_sn_rx = 0
        initial_energy_ch_tx = initial_energy_ch_rx = 0
        initial_energy_sn_tx = initial_energy_sn_rx = 0

        # while retries_ChtoSn < max_retries_sensor and not node["IsSynced"]:
        while retries_ChtoSn < max_retries_sensor and not ack_received_CH:
            # Aqui toca agregar el delay de propagación basasdo en la formula de distancia/velocidad
            # delay = random_sync_delay()  # Generar un tiempo de retraso aleatorio
            # calcular la distancia entre los nodos
            dist = np.linalg.norm(node["Position"] - node_uw[CH_id]["Position"])    # se debe comentar 10/09/2025
            start_position = node["Position"]
            end_position = node_uw[CH_id]["Position"]
            #delay = propagation_time(dist, start_position, end_position)    # se comenta 10/09/2025
            delay = propagation_time1(start_position, end_position, depth=None, region="standard")

            print(f"Sincronizando nodo {node['NodeID']} bajo el Cluster Head {CH_id + 1} con un retraso de {delay:.2f} segundos, distancia calculada {dist:.2f}")
            # time.sleep(delay)  # Simular el tiempo de sincronización

            # PER desde CH al nodo
            per_ch_sn, SL_db, snr_db, EbN0_db, ber = per_from_link(f_khz=20, distance_m=dist, L=PACKET_SIZE_SYN, bitrate=9200)
            # succesks_rx = np.random.rand() > 0.3
            success_tx = propagate_with_probability(per=per_ch_sn, override_per=PER_VARIABLE)
            p_lost_tx = not success_tx
            bits_received = PACKET_SIZE_SYN if success_tx else 0

            # Calcular el timeout de espera
            lat_prop, lat_tx, lat_proc, timeout_chtosn = calculate_timeout(node_uw[CH_id]["Position"], node["Position"], 
                                                                           bitrate=9200, packet_size=PACKET_SIZE_SYN)

            # CH transmite el paquete de sincronización
            initial_energy_ch_tx = node_uw[CH_id]["ResidualEnergy"] 
            node_uw[CH_id] = update_energy_node_tdma(node_uw[CH_id], node["Position"], E_schedule, timeout_chtosn, 
                                                     type_packet, role='CH', action='tx', verbose=VERBOSE)
            energy_consumed_ch_tx = ((initial_energy_ch_tx - node_uw[CH_id]["ResidualEnergy"]))
            
            log_event(
                run_id=RUN_ID, phase="sync", module="syn_light", msg_type="SYN:TDMA",
                sender_id=node_uw[CH_id]["NodeID"], receiver_id=node["NodeID"], cluster_id=node["ClusterHead"],
                start_pos=start_position, end_pos=end_position,
                bits_sent=PACKET_SIZE_SYN, bits_received=bits_received,
                success=success_tx, packet_lost=p_lost_tx, 
                energy_event_type='tx', energy_j=energy_consumed_ch_tx,
                residual_sender=node_uw[CH_id]["ResidualEnergy"], residual_receiver=node["ResidualEnergy"],
                bitrate=9200, freq_khz=20,
                lat_prop_ms=lat_prop, lat_tx_ms=lat_tx, lat_proc_ms=lat_proc,
                snr_db=snr_db, per=per_ch_sn,
                lat_dag_ms=0.0, SL_db=SL_db, EbN0_db=EbN0_db, BER=ber
                )
            
            # Los nodos consumen cuando no estan transmitiendo.
            active_ids = [node_uw[CH_id]["NodeID"],  node["NodeID"]]
            active_cluster_id = node_uw[CH_id]["ClusterHead"]
            node_uw = update_energy_standby_others(node_uw, active_ids, active_cluster_id, timeout_chtosn, verbose=VERBOSE)
            
            if success_tx:
                ack_received_CH = True
                print("El nodo recibio el paquete de syn...")
                # Nodo recibe el paquete
                initial_energy_sn_rx = node["ResidualEnergy"]
                node = update_energy_node_tdma(node, node_uw[CH_id]["Position"], E_schedule, timeout_chtosn, 
                                               type_packet, role='SN', action='rx', verbose=VERBOSE)
                energy_consumed_sn_rx = (initial_energy_sn_rx - node["ResidualEnergy"])

                log_event(
                    run_id=RUN_ID, phase="sync", module="syn_light", msg_type="SYN:TDMA",
                    sender_id=node_uw[CH_id]["NodeID"], receiver_id=node["NodeID"], cluster_id=node["ClusterHead"],
                    start_pos=start_position, end_pos=end_position,
                    bits_sent=PACKET_SIZE_SYN, bits_received=bits_received, payload_bits=0,
                    success=success_tx, packet_lost=p_lost_tx, 
                    energy_event_type='rx', energy_j=energy_consumed_sn_rx,
                    residual_sender=node_uw[CH_id]["ResidualEnergy"], residual_receiver=node["ResidualEnergy"],
                    bitrate=9200, freq_khz=20,
                    lat_prop_ms=lat_prop, lat_tx_ms=lat_tx, lat_proc_ms=lat_proc,
                    snr_db=snr_db, per=per_ch_sn,
                    lat_dag_ms=0.0, SL_db=SL_db, EbN0_db=EbN0_db, BER=ber
                )

                while ack_retries < max_retries_sensor and not ack_received_node:
                    # Nodo responde con ACK (también puede fallar)
                    per_sn_ch, SL_db, snr_db, EbN0_db, ber = per_from_link(f_khz=20, distance_m=dist, L=PACKET_SIZE_SYN, bitrate=9200)
                    success_ack = propagate_with_probability(per=per_sn_ch, override_per=PER_VARIABLE)
                    p_lost_ack = not success_ack
                    bits_sent_ack = PACKET_SIZE_SYN

                    initial_energy_sn_tx = node["ResidualEnergy"]
                    node = update_energy_node_tdma(node, node_uw[CH_id]["Position"], E_schedule, timeout_chtosn, 
                                                   type_packet, role='SN', action='tx', verbose=VERBOSE)
                    energy_consumed_sn_tx = (initial_energy_sn_tx - node["ResidualEnergy"])            

                    log_event(
                        run_id=RUN_ID, phase="sync", module="syn_light", msg_type="SYN:TDMA:ACK",
                        sender_id=node["NodeID"], receiver_id=node_uw[CH_id]["NodeID"], cluster_id=node["ClusterHead"],
                        start_pos=start_position, end_pos=end_position,
                        bits_sent=bits_sent_ack, bits_received=bits_received,
                        success=success_ack, packet_lost=p_lost_ack, 
                        energy_event_type='tx', energy_j=energy_consumed_sn_tx,
                        residual_sender=node["ResidualEnergy"], residual_receiver=node_uw[CH_id]["ResidualEnergy"],
                        bitrate=9200, freq_khz=20,
                        lat_prop_ms=lat_prop, lat_tx_ms=lat_tx, lat_proc_ms=lat_proc,
                        snr_db=snr_db, per=per_sn_ch,
                        lat_dag_ms=0.0, SL_db=SL_db, EbN0_db=EbN0_db, BER=ber
                    )

                    # Los nodos consumen cuando no estan transmitiendo.
                    active_ids = [node_uw[CH_id]["NodeID"],  node["NodeID"]]
                    active_cluster_id = node_uw[CH_id]["ClusterHead"]
                    node_uw = update_energy_standby_others(node_uw, active_ids, active_cluster_id, timeout_chtosn, verbose=VERBOSE)
                    
                    if success_ack:
                        print(f"Nodo {node['NodeID']} sincronizado exitosamente.")
                        ack_received_node = True
                        node["IsSynced"] = True  # Marcar el nodo como sincronizado

                        # Actualizar la energía del Cluster Head
                        initial_energy_ch_rx = node_uw[CH_id]["ResidualEnergy"] 
                        node_uw[CH_id] = update_energy_node_tdma(node_uw[CH_id], node["Position"], E_schedule, timeout_chtosn, 
                                                                 type_packet, role='CH', action='rx', verbose=VERBOSE)
                        energy_consumed_ch_rx = (initial_energy_ch_rx - node_uw[CH_id]["ResidualEnergy"])
                        
                        log_event(
                            run_id=RUN_ID, phase="sync", module="syn_light", msg_type="SYN:TDMA:ACK",
                            sender_id=node["NodeID"], receiver_id=node_uw[CH_id]["NodeID"], cluster_id=node["ClusterHead"],
                            start_pos=start_position, end_pos=end_position,
                            bits_sent=bits_sent_ack, bits_received=bits_received, payload_bits=0,
                            success=success_ack, packet_lost=p_lost_ack, 
                            energy_event_type='rx', energy_j=energy_consumed_ch_rx,
                            residual_sender=node["ResidualEnergy"], residual_receiver=node_uw[CH_id]["ResidualEnergy"],
                            bitrate=9200, freq_khz=20,
                            lat_prop_ms=lat_prop, lat_tx_ms=lat_tx, lat_proc_ms=lat_proc,
                            snr_db=snr_db, per=per_sn_ch,
                            lat_dag_ms=0.0, SL_db=SL_db, EbN0_db=EbN0_db, BER=ber
                        )
                        
                        # Registrar el nodo como sincronizado en el CH
                        register_node_to_ch(CH_id, node["NodeID"], node["IsSynced"], False, node_uw)  # Aquí asumimos que aún no está autenticado
                    else:
                        print(f"Nodo {node['NodeID']} falló en sincronizarse, intento {retries_ChtoSn+1}")
                        ack_retries += 1
                        # Actualiza la energía del nodo en caso de no recibir el pkt, pero esta escuchando en su slot
                        node_uw[CH_id] = update_energy_failed_rx(node_uw[CH_id], node["Position"], timeout_chtosn, 
                                                                 role="CH", verbose=VERBOSE)

            else:
                print(f"Nodo {node['NodeID']} falló en sincronizarse, intento {retries_ChtoSn+1}")
                retries_ChtoSn += 1
                # Actualiza la energía del nodo en caso de no recibir el pkt, pero esta escuchando en su slot
                node = update_energy_failed_rx(node, node_uw[CH_id]["Position"], timeout_sinktoch, role="SN", verbose=VERBOSE)
                # time.sleep(timeout_node)  # Retransmitir con timeout     

        # sync_end_time_node = time.time() - start_time_node

        if not node["IsSynced"] and retries_ChtoSn == max_retries_sensor:
            print(f"Nodo {node['NodeID']} no pudo sincronizarse después de {retries_ChtoSn} intentos.")

    return # node_stats  # ACK del CH fue recibido correctamente












#############################################################
#############################################################
#############################################################
#REVISAR CDMA

# Para calcular el tiempo de propagación de una señal acústica en un entorno subacuático, se puede usar la fórmula
# t = d / v
#donde:
# 𝑡 = es el tiempo de propagación (en segundos),
# 𝑑 = es la distancia entre el emisor y el receptor (en metros),
# 𝑣 = es la velocidad del sonido en el agua (en metros por segundo).
# # La velocidad del sonido en el agua puede variar dependiendo de la temperatura, la salinidad y la presión.


## Funciones adicionales

# CAMBIAR FUNCIÓN
# Función de pérdida acústica (implementada previamente)
def acoustic_loss(dist, freq):
    spreading_factor = 1.5  # Factor de propagación
    # Devuelve la perdida total en dB
    loss_db, loss_factor = compute_path_loss(freq, dist, spreading_factor)
    return loss_db, loss_factor

# IMPLEMENTADO CDMA

# Función para actualizar la energía de un nodo basado en CDMA (considerando que solo los CH realizan EDA)
def update_energy_node_cdma(node, target_pos, packet_size_bits, alpha, P_r, freq, processing_energy_cdma):
    """
    Actualiza la energía del nodo basado en su distancia al CH o Sink y el esquema CDMA.
    Parámetros:
    node: El nodo a actualizar.
    target_pos: Posición del objetivo (CH o Sink).
    packet_size_bits: Tamaño del paquete en bits.
    alpha: Factor de energía por distancia.
    P_r: Potencia de recepción.
    freq: Frecuencia de transmisión acústica.
    processing_energy_cdma: Energía consumida por procesamiento en CDMA.
    is_ch: Indica si el nodo es un Cluster Head (True/False).
    
    Actualiza el campo ResidualEnergy del nodo.
    """
    dist = np.linalg.norm(node["Position"] - target_pos)  # Distancia entre el nodo y el objetivo
    
    # Corregir esta con la formula de thorp
    loss = acoustic_loss(dist, freq)  # Pérdida acústica entre el nodo y el objetivo

    Et = packet_size_bits * (alpha * 10**(loss / 10))  # Energía de transmisión

    # Energía de recepción
    Er = P_r * packet_size_bits
    # Energía adicional por procesamiento en CDMA (codificación/decodificación)
    processing_energy = processing_energy_cdma * packet_size_bits

    # Actualizar la energía residual del nodo
    node["ResidualEnergy"] -= (Et + Er + processing_energy)
    
    # Evitar que la energía se vuelva negativa
    if node["ResidualEnergy"] < 0:
        node["ResidualEnergy"] = 0

    return node


# Función para propagar el paquete SYN y actualizar la energía de los nodos bajo CDMA
def propagate_syn_to_CH_cdma(sink, CH_ids, node_uw, max_retries=3, timeout=2, freq=20, processing_energy_cdma=5e-9, packet_size_bits=100,alpha=1e-6, Ptr=1e-3, E_listen=1e-9, E_standby=1e-12):
    timestamp = time.perf_counter()  # Marca de tiempo actual en segundos
    syn_packet = create_syn_packet(sink["NodeID"])

    # # Parámetros de energía enviados, para ser enviados a los nodos del cluster
    max_retries_sensor = max_retries
    time_node = timeout
    freq_node = freq
    process_eng_cdma = processing_energy_cdma
    packet_control = packet_size_bits
    alpha_node = alpha
    Ptr_node = Ptr
    E_listen_node = E_listen
    E_standby_node = E_standby

    # Diccionario para almacenar estadísticas individuales
    stats = {
        "sync_stats": {},  # Para guardar estadísticas por cada CH y nodo
    }

    # Intentar sincronizar cada CH
    for ch in CH_ids:
        retries = 0
        ack_received_CH = False
        # Estadistica
        start_time = time.perf_counter()  # Tiempo de inicio de la sincronización
        energy_consumed_ch = 0  # Para capturar la energía consumida por el CH

        while retries < max_retries and not ack_received_CH:
            print(f"Enviando paquete SYN del Sink {sink['NodeID']} al Cluster Head {ch + 1} (Intento {retries+1})")
            # syn_packet["Hops"] += 1  # Aumentar el contador de saltos
            
            # Aqui toca agregar el delay de propagación basasdo en la formula de distancia/velocidad
            # delay = random_sync_delay()  # Generar un tiempo de retraso aleatorio
            # calcular la distancia entre los nodos
            dist = np.linalg.norm(node_uw[ch]["Position"] - sink["Position"]) # se debe comentar 10/09/2025
            
            start_position = sink["Position"]
            end_position = node_uw[ch]["Position"]
            # delay = propagation_time(dist, start_position, end_position)    # se comenta 10/09/2025
            delay = propagation_time1(start_position, end_position, depth=None, region="standard")

            print(f"Sincronizando el CH {node_uw[ch]['NodeID']} bajo el Sink, retraso de {delay:.2f} segundos, distancia calculada {dist:.2f}")
            # time.sleep(delay)  # Simular el tiempo de sincronización

            # **Nuevo: Medir energía inicial del CH**
            initial_energy = node_uw[ch]["ResidualEnergy"]

            # Actualizar la energía del Cluster Head
            node_uw[ch] = update_energy_node_cdma(node_uw[ch], sink["Position"], packet_control, alpha_node, Ptr_node, freq_node, process_eng_cdma)
            
            # **Nuevo: Calcular la energía consumida**
            energy_consumed_ch += ((initial_energy - node_uw[ch]["ResidualEnergy"]) + E_listen)

            # Simulación de recepción de ACK para el CH, se considera 0 como escenario ideal
            # Pero se puede manejar una probabilidad de acuerdo a otros estudios
            # En este caso no van a existir retransmisisones
            ack_received_CH = np.random.rand() > 0

            if not ack_received_CH:
                print(f"Cluster Head {ch + 1} no envió ACK, posible retransmisión necesaria.")
                retries += 1
                # Esto se debe cambiar por la función de delay nueva que calcula el delay de propagación
                # basado en distancia / velocidad
                time.sleep(timeout)  # Esperar antes de retransmitir (simulando backoff)
            else:
                # print(f"Cluster Head {ch + 1} sincronizado exitosamente.")
                node_uw[ch]["IsSynced"] = True  # Marcar el nodo como sincronizado

                # Se repite el delay de respuesta del sink hacia el nodo CH
                # Aqui toca agregar el delay de propagación basasdo en la formula de distancia/velocidad
                # delay = random_sync_delay()  # Generar un tiempo de retraso aleatorio
                # calcular la distancia entre los nodos
                dist = np.linalg.norm(node_uw[ch]["Position"] - sink["Position"])   # se debe comentar 10/09/2025
                
                start_position = sink["Position"]
                end_position = node_uw[ch]["Position"]
                # delay = propagation_time(dist, start_position, end_position)    # se comenta 10/09/2025
                delay = propagation_time1(start_position, end_position, depth=None, region="standard")

                print(f"CH {node_uw[ch]['NodeID']} sicronizado exitosamente bajo el Sink, retraso de {delay:.2f} segundos, distancia calculada {dist:.2f}")
                # time.sleep(delay)  # Simular el tiempo de sincronización

                # Si el CH se sincroniza exitosamente el Sink lo habilita como sincronizado
                sink['RegisterNodes'][ch]['Status_syn'] = True

                # Capturar estadísticas de sincronización
                sync_end_time = time.time() - start_time
                stats["sync_stats"][f"CH_{node_uw[ch]['NodeID']}"] = {
                    "energy_consumed": energy_consumed_ch,
                    "sync_time": sync_end_time * 1000, # Milisegundos
                    "retransmissions": retries,
                    "is_syn": node_uw[ch]["IsSynced"]
                }

                node_stats = synchronize_nodes_cdma(ch, syn_packet, node_uw, time_node, freq_node, process_eng_cdma, max_retries_sensor, packet_control, alpha_node, Ptr_node, E_listen_node, E_standby_node)

                # Agregar las estadísticas individuales de nodos al diccionario principal
                stats["sync_stats"].update(node_stats)

        if not node_uw[ch]["IsSynced"] and retries == max_retries:
            print(f"CH {node_uw[ch]['NodeID']} no pudo sincronizarse después de {retries} intentos.")

    return syn_packet, stats



# Función para sincronizar nodos con el Cluster Head bajo CDMA, incluyendo retransmisiones
def synchronize_nodes_cdma(CH_id, syn_packet, node_uw, timeout, freq, processing_energy_cdma, max_retries_sensor, packet_size_bits, alpha, P_r, E_listen, E_standby):
    
    # print(f"Sincronizando Cluster Head {CH_id + 1} con Timestamp: {syn_packet['Timestamp']} y Hops: {syn_packet['Hops']}")
    print(f"Sincronizando Cluster Head {CH_id + 1} con Timestamp: {syn_packet['Timestamp']}")

    # Filtrar los nodos que tienen a este CH como su ClusterHead y que no sean el propio CH
    cluster_nodes = [node for node in node_uw if node["ClusterHead"] == (CH_id + 1) and node["NodeID"] != (CH_id + 1)]

    print(cluster_nodes)

    # Variables para contar cuántos nodos se sincronizan y cuántos fallan
    node_stats = {} # Diccionario para almacenar estadísticas de cada nodo

    # Si ACK es recibido, propagar la sincronización a los nodos del clúster
    for node in cluster_nodes:
        retries = 0
        ack_received_node = False
        start_time_node = time.time()
        energy_consumed_node = 0

        while retries < max_retries_sensor and not node["IsSynced"]:
            # Aqui toca agregar el delay de propagación basasdo en la formula de distancia/velocidad
            # delay = random_sync_delay()  # Generar un tiempo de retraso aleatorio
            # calcular la distancia entre los nodos
            dist = np.linalg.norm(node["Position"] - node_uw[CH_id]["Position"])    # se debe comentar 10/09/2025
            
            start_position = node["Position"]
            end_position = node_uw[CH_id]["Position"]
            # delay = propagation_time(dist, start_position, end_position)    # se comenta 10/09/2025
            delay = propagation_time1(start_position, end_position, depth=None, region="standard")

            print(f"Sincronizando nodo {node['NodeID']} bajo el Cluster Head {CH_id + 1}, retraso de {delay:.2f} segundos, distancia calculada {dist:.2f}")
            # time.sleep(delay)  # Simular el tiempo de sincronización

            initial_energy = node["ResidualEnergy"]
            # Actualizar la energía del nodo sensor (sin EDA)
            print('Actualizando energia del nodo : ', node["NodeID"], '-> Posoción del nodo : ', node["Position"], ' -> en relación al ch :', node_uw[CH_id]['NodeID'], ' -> En la posición : ', node_uw[CH_id]["Position"])
            
            node = update_energy_node_cdma(node, node_uw[CH_id]["Position"], packet_size_bits, alpha, P_r, freq, processing_energy_cdma)
            energy_consumed_node += ((initial_energy - node["ResidualEnergy"]) + E_listen)

            # Simulación de recepción de ACK para el CH, se considera 0 como escenario ideal
            # Pero se puede manejar una probabilidad de acuerdo a otros estudios
            # En este caso no van a existir retransmisisones
            ack_received_node = np.random.rand() > 0

            if ack_received_node:
                node["IsSynced"] = True  # Marcar el nodo como sincronizado

                # Registrar el nodo como sincronizado en el CH
                register_node_to_ch(CH_id, node["NodeID"], node["IsSynced"], False, node_uw)  # Aquí asumimos que aún no está autenticado
                
                # Se repite el delay de respuesta del nodo hacia el nodo CH
                # Aqui toca agregar el delay de propagación basasdo en la formula de distancia/velocidad
                # delay = random_sync_delay()  # Generar un tiempo de retraso aleatorio
                # calcular la distancia entre los nodos
                dist = np.linalg.norm(node["Position"] - node_uw[CH_id]["Position"])    # se debe comentar 10/09/2025
                
                start_position = node["Position"]
                end_position = node_uw[CH_id]["Position"]
                #delay = propagation_time(dist, start_position, end_position)    # se comenta 10/09/2025
                delay = propagation_time1(start_position, end_position, depth=None, region="standard")

                print(f"Nodo {node['NodeID']} sincronizado exitosamente bajo el Cluster Head {CH_id + 1}, retraso de {delay:.2f} segundos, distancia calculada {dist:.2f}")
                # time.sleep(delay)  # Simular el tiempo de sincronización

            else:
                print(f"Nodo {node['NodeID']} falló en sincronizarse, intento {retries+1}")
                retries += 1
                # time.sleep(timeout)  # Retransmitir con timeout
        
        # Registrar tiempo total de sincronización para el nodo
        sync_end_time_node = time.time() - start_time_node

        # Guardar las estadísticas del nodo en el diccionario
        
        node_stats[f"Node_{node['NodeID']}"] = {
            "energy_consumed": energy_consumed_node,
            "sync_time": sync_end_time_node * 1000, # Milisegudnos
            "retransmissions": retries,
            "is_syn": node["IsSynced"]
        }

        if not node["IsSynced"]:
            print(f"Nodo {node['NodeID']} no pudo sincronizarse después de {retries} intentos.")

    return  node_stats  # ACK del CH fue recibido correctamente


# Consumo de energía en modo escucha 
def update_energy_listen(node, E_listen):
    """
    Actualiza la energía del nodo por estar escuchando el medio (en espera de sincronización).
    Parámetros:
    node: Nodo a actualizar.
    E_listen: Energía consumida por escuchar el medio.
    """
    node["ResidualEnergy"] -= E_listen  # Disminuye la energía por escuchar el medio
    # Evitar que la energía se vuelva negativa
    if node["ResidualEnergy"] < 0:
        node["ResidualEnergy"] = 0

    return node


def clear_sync_state(nodo_sink, node_uw, CH):
    """
    Restablece el estado de sincronización de todos los nodos en node_uw.
    """
    # Restablecer el estado de autenticación en nodo_sink
    for i in range(len(nodo_sink['RegisterNodes'])):
        nodo_sink['RegisterNodes'][i]['Status_syn'] = False
        # nodo_sink['RegisterNodes'][i]['Status_auth'] = False

    #print(" node sink : ", nodo_sink)

    # Restablecer el estado de autenticación de cada nodo CH
    for ch_index in CH:
        for i in range(len(node_uw[ch_index]['RegisterNodes'])):
            #print("ch_index : ", ch_index, " i : ", i, " len : ", len(node_uw[ch_index]['RegisterNodes']))
            node_uw[ch_index]['RegisterNodes'][i]['Status_syn'] = False
            # node_uw[ch_index]['RegisterNodes'][i]['Status_auth'] = False
        
        node_uw[ch_index]["RegisterNodes"] = [] # Eliminar los registros del CH

    for node in node_uw:
        node['IsSynced'] = False

    print('Estado de sincronización de todos los nodos eliminado...')


# # Limpiar los registros de nodos cuando ya no sea CH
# def clear_register_nodes(ch_id, node_uw):
#     node_uw[ch_id]["RegisterNodes"] = []