import sqlite3
import random
# from transmission_logger import log_transmission_event
from energia_dinamica import (calcular_energia_paquete, energy_listen, energy_standby, 
                              calculate_timeout, update_energy_node_tdma, estimate_proc_time_s, 
                              update_energy_standby_others, update_energy_failed_rx)
from per_from_link_uan import per_from_link, propagate_with_probability
from transmission_logger_uan import log_event

global VERBOSE

PER_VARIABLE = None
VERBOSE = False
PAYLOAD_BITS_SN = 60*8 # 480 bits
PAYLOAD_BITS_CH = 92*8 # 736 bits

# Crea la tabla para almacenar las claves compartidas en la BBDD del nodo
def create_shared_keys_table(db_path):

    # Obtener la ruta del directorio donde se encuentra el script actual
    # current_dir = os.path.dirname(os.path.abspath(__file__))
    current_dir = os.getcwd()
    
    # Definir la carpeta donde quieres guardar el archivo (carpeta 'data')
    carpeta_destino = os.path.join(current_dir, 'data')

    # Crea la carpeta en caso de no existir
    if not os.path.exists(carpeta_destino):
        os.makedirs(carpeta_destino)

    # Ruta completa del archivo de la base de datos dentro de la carpeta 'data'
    ruta_bbdd = os.path.join(carpeta_destino, db_path)

    conn = sqlite3.connect(ruta_bbdd)
    cursor = conn.cursor()

    # conn = sqlite3.connect(db_path)
    # cursor = conn.cursor()
    
    # Eliminar la tabla si ya existe
    cursor.execute("DROP TABLE IF EXISTS shared_keys")

    # Crear la tabla desde cero
    cursor.execute('''CREATE TABLE shared_keys (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        node_id INTEGER,
                        peer_id INTEGER,
                        shared_key BLOB,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')

    conn.commit()
    conn.close()

# Obtiene las claves de la BBDD del nodo, con el ID de clave
def get_x25519_keys(db_path, key_id):
    # """Obtiene las claves X25519 de la base de datos usando el ID aleatorio asignado."""
    # conn = sqlite3.connect(db_path)
    # cursor = conn.cursor()

    # Obtener la ruta del directorio donde se encuentra el script actual
    # current_dir = os.path.dirname(os.path.abspath(__file__))
    current_dir = os.getcwd()
    
    # Definir la carpeta donde quieres guardar el archivo (carpeta 'data')
    carpeta_destino = os.path.join(current_dir, 'data')

    # Crea la carpeta en caso de no existir
    if not os.path.exists(carpeta_destino):
        os.makedirs(carpeta_destino)

    # Ruta completa del archivo de la base de datos dentro de la carpeta 'data'
    ruta_bbdd = os.path.join(carpeta_destino, db_path)

    conn = sqlite3.connect(ruta_bbdd)
    cursor = conn.cursor()

    cursor.execute("SELECT clave_publica, clave_privada FROM keys_shared_x25519 WHERE id = ?", (key_id,))
    row = cursor.fetchone()
    conn.close()
    return row if row else (None, None)


from cryptography.hazmat.primitives.asymmetric import x25519

# Realiza la derivación de la clave, tomando la clave privada del nodo source y
# la clave publica de nodo destination
def derive_shared_key(x_priv_bytes, peer_x_pub_bytes):
    """Deriva una clave compartida usando X25519."""
    private_key = x25519.X25519PrivateKey.from_private_bytes(x_priv_bytes)
    peer_public_key = x25519.X25519PublicKey.from_public_bytes(peer_x_pub_bytes)
    return private_key.exchange(peer_public_key)


# Almacena la clave compartida en la tabla respectiva
def store_shared_key(db_path, node_id, peer_id, shared_key):
    # """Guarda la clave compartida en la base de datos."""
    # conn = sqlite3.connect(db_path)
    # cursor = conn.cursor()

    # Obtener la ruta del directorio donde se encuentra el script actual
    # current_dir = os.path.dirname(os.path.abspath(__file__))
    current_dir = os.getcwd()
    
    # Definir la carpeta donde quieres guardar el archivo (carpeta 'data')
    carpeta_destino = os.path.join(current_dir, 'data')

    # Crea la carpeta en caso de no existir
    if not os.path.exists(carpeta_destino):
        os.makedirs(carpeta_destino)

    # Ruta completa del archivo de la base de datos dentro de la carpeta 'data'
    ruta_bbdd = os.path.join(carpeta_destino, db_path)

    conn = sqlite3.connect(ruta_bbdd)
    cursor = conn.cursor()

    cursor.execute("INSERT INTO shared_keys (node_id, peer_id, shared_key) VALUES (?, ?, ?)",
                   (int(node_id), int(peer_id), shared_key))
    conn.commit()
    conn.close()

# Función para generar claves compartidas desde el soruce al destination
def generate_shared_keys(db_path, node_uw, CH, node_sink):
    """Genera claves compartidas considerando los ID aleatorios asignados a cada nodo."""
    for node in node_uw:
        node_id = node["NodeID"]
        key_id = node["Id_pair_keys_shared"]  # ID de clave aleatoria
        ch_id = node["ClusterHead"]
        # if_node_ch = 0
        
        # Obtner clave del sink
        x_pub_sink = node_sink["PublicKey_shared"]

        # Evitar que el nodo genere una clave con él mismo
        if node_id == ch_id:
            # print(f"⚠️ Nodo {node_id} es un CH y no generará clave consigo mismo.")
            # print(f"⚠️ Nodo {node_id} es un CH...")

            # Obtener claves del nodo y su Cluster Head
            x_pub_node, x_priv_node = get_x25519_keys(db_path, key_id)

            shared_key = derive_shared_key(x_priv_node, x_pub_sink)

            #print("db_path : ", db_path, "node_id : ", node_id, "node_sink[NodeID] : ", node_sink["NodeID"], "shared_key : ", shared_key.hex())
            store_shared_key(db_path, node_id, node_sink["NodeID"], shared_key)
            # print(f"🔐 CH {node_id} generó clave compartida con el Sink", shared_key.hex())
            # if_node_ch = 1
            continue
        # else:
        #     if_node_ch = 2

        # Obtener claves del nodo y su Cluster Head
        x_pub_node, x_priv_node = get_x25519_keys(db_path, key_id)
        ch_key_id = next(n["Id_pair_keys_shared"] for n in node_uw if n["NodeID"] == ch_id)
        x_pub_ch, _ = get_x25519_keys(db_path, ch_key_id)

        # Obtener claves del Sink (única clave)
        # sink_key_id = node_sink["Id_pair_keys_shared"]
        # x_pub_sink, _ = get_x25519_keys(db_path, sink_key_id)

        if x_priv_node and x_pub_ch:

            shared_key = derive_shared_key(x_priv_node, x_pub_ch)

            #print("db_path : ", db_path, "node_id : ", node_id, "ch_id : ", ch_id, "shared_key : ", shared_key.hex())
            store_shared_key(db_path, node_id, ch_id, shared_key)
            # print(f"🔐 Nodo {node_id} generó clave compartida con CH {ch_id}", shared_key.hex())

        #if node_id in CH:  # Si el nodo es un CH, genera clave con el Sink
            

from ascon import encrypt, decrypt
import os

def encrypt_message(shared_key, plaintext):
    """Cifra un mensaje con ASCON-128 usando la clave compartida."""
    key = shared_key[:16]  # ASCON-128 requiere 16 bytes de clave
    nonce = os.urandom(16)
    associated_data = b""
        # Detectar si es str o bytes
    if isinstance(plaintext, str):
        plaintext_bytes = plaintext.encode('utf-8')
    elif isinstance(plaintext, bytes):
        plaintext_bytes = plaintext
    else:
        raise TypeError("El parámetro 'plaintext' debe ser str o bytes")

    ciphertext = encrypt(key, nonce, associated_data, plaintext_bytes, variant="Ascon-128")
    # print("ciphertext : ", ciphertext, " Len : ", len(ciphertext), "nonce : ", nonce, " Len : ", len(nonce))
    return nonce + ciphertext

def decrypt_message(shared_key, encrypted_message):
    """Descifra un mensaje con ASCON-128."""
    key = shared_key[:16]
    nonce, ciphertext = encrypted_message[:16], encrypted_message[16:]
    associated_data = b""

    decrypted = decrypt(key, nonce, associated_data, ciphertext, variant="Ascon-128")

    try:
        # Intentar decodificar como texto UTF-8
        return decrypted.decode('utf-8')
    except UnicodeDecodeError:
        # Si no es texto, devolver como binario
        return decrypted


import time
import numpy as np
# from test_throp import propagation_time, compute_path_loss, propagation_time1
from path_loss import propagation_time, compute_path_loss, propagation_time1

# data_packet = {
#     "PacketType": 0x03,           # Identificador de tipo DATA
#     "SourceID": node_id,          # Nodo que envía el paquete
#     "Timestamp": current_time,    # Marca de tiempo local
#     "EncryptedPayload": cipher_text,  # Datos cifrados con Ascon
#     "Tag": tag                    # Tag de autenticación (si no está embebido)
# }

# agg_packet = {
#     "PacketType": 0x04,           # Tipo de paquete agregado
#     "ClusterID": ch_id,           # Identificador del CH
#     "Timestamp": current_time,    # Marca de tiempo de envío
#     "PayloadCount": N,            # Número de paquetes agregados
#     "AggregatedPayload": encrypted_blob  # Cifrado conjunto (JSON/lista cifrada)
# }


# def transmit_data_anterior(db_path, sender_id, receiver_id, plaintext, E_schedule, source='SN', dest='CH'):
#     # """Simula la transmisión de datos cifrados entre nodos usando claves compartidas almacenadas en la base de datos."""
#     # conn = sqlite3.connect(db_path)
#     # cursor = conn.cursor()

#     if source == 'SN' and dest == 'CH':
#         msg_type = type_packet = 'data'
#     elif source == 'CH' and dest == 'Sink':
#         msg_type = type_packet = 'agg'
#     # else:
#     #     msg_type = type_packet = 'sync'     # Simula el paquete de ack
    
#     energy_consumed_sn = 0
#     energy_consumed_ch = 0
#     initial_energy_sn = 0
#     initial_energy_ch = 0

#     energy_consumed_sn_tx = energy_consumed_sn_rx = 0
#     energy_consumed_ch_tx = energy_consumed_ch_rx = 0
#     initial_energy_sn_tx = initial_energy_sn_rx = 0
#     initial_energy_ch_tx = initial_energy_ch_rx = 0

#     # Obtener la ruta del directorio donde se encuentra el script actual
#     # current_dir = os.path.dirname(os.path.abspath(__file__))
#     current_dir = os.getcwd()
    
#     # Definir la carpeta donde quieres guardar el archivo (carpeta 'data')
#     carpeta_destino = os.path.join(current_dir, 'data')

#     # Crea la carpeta en caso de no existir
#     if not os.path.exists(carpeta_destino):
#         os.makedirs(carpeta_destino)

#     # Ruta completa del archivo de la base de datos dentro de la carpeta 'data'
#     ruta_bbdd = os.path.join(carpeta_destino, db_path)

#     conn = sqlite3.connect(ruta_bbdd)
#     cursor = conn.cursor()

#     sender = sender_id["NodeID"]
#     receiver = receiver_id["NodeID"]

#     #print("Dentro de la función transmit data : ", sender, "-->", receiver)

#     # Obtener la clave compartida entre los nodos
#     # cursor.execute("SELECT shared_key FROM shared_keys WHERE node_id = ? AND peer_id = ?", (sender_id, receiver_id)) # accede al dato tipo blob
#     cursor.execute("SELECT shared_key, id FROM shared_keys WHERE node_id = ? AND peer_id = ?", (int(sender), int(receiver))) # accede al dato tipo int
#     row = cursor.fetchone()
#     conn.close()

#     if row:
#         shared_key = row[0]
#         shared_key_id = row[1]

#         start_time_enc = time.perf_counter()
#         encrypted_msg = encrypt_message(shared_key, plaintext)
#         end_time_enc = time.perf_counter()
#         time_encryp = end_time_enc - start_time_enc
#         print(f"📡 {sender} → {receiver} | 🔐 Cifrado: {encrypted_msg.hex()[:20]}...")
        
#         start_time_dec = time.perf_counter()
#         decrypted_msg = decrypt_message(shared_key, encrypted_msg)
#         end_time_dec = time.perf_counter()
#         time_descryp = end_time_dec - start_time_dec

#         print(f"📡 {sender} → {receiver} | 📥 Descifrado: {decrypted_msg}")
        
#         # Simulación de retardo en la propagación acústica
#         # distance = np.random.uniform(100, 1000)  # Distancia aleatoria entre nodos
#         distance = np.linalg.norm(sender_id["Position"] - receiver_id["Position"])  # se debe comentar 10/09/2025
#         start_position = sender_id["Position"]
#         end_position = receiver_id["Position"]

#         #delay = propagation_time(distance, start_position, end_position)    # se comenta 10/09/2025
#         delay = propagation_time1(start_position, end_position, depth=None, region="standard")
#         print(f"delay of propagation data :  {delay}")
#         # time.sleep(delay)

#         latency_ms = ((end_time_enc - start_time_enc) + delay + (end_time_dec - start_time_dec) + 0.02) * 1000  # en milisegundos
#         latency_encryp_ms = ((end_time_enc - start_time_enc) + delay + 0.02) * 1000  # en milisegundos
#         latency_dec_ms = ( delay + (end_time_dec - start_time_dec) + 0.02) * 1000  # en milisegundos

#         # bits_sent = len(plaintext.encode()) * 8
#         bits_sent = len(encrypted_msg) * 8
#         bits_received = len(encrypted_msg) * 8
        
#         # Simular pérdida de paquetes
#         per_data, SL_db, snr_db, EbN0_db, ber = per_from_link(f_khz=20.0, distance_m=distance, L=bits_sent, bitrate=9200)
#         #success = random.random() > 0.05  # 95% éxito

#         if not per_data:
#             # p_lost = not success
#             p_lost = True
#             print("⚠️ Paquete perdido durante la transmisión simulada", p_lost)
#         else:
#             p_lost = False

#         if source == 'SN' and dest == 'CH':
#             # Energia antes de la trasmisión
#             # **Nuevo: Medir energía inicial del CH**
#             initial_energy_sn = sender_id['ResidualEnergy']
#             print('Energía inicial antes de actualizar el nodo : ', initial_energy_sn)

#             # Calcular el timeout de espera
#             lat_prop, lat_tx, lat_proc, timeout = calculate_timeout(start_position, end_position, bitrate=9200, 
#                                                                     packet_size=bits_sent)
#             sender_id = update_energy_node_tdma(sender_id, receiver_id["Position"], E_schedule, timeout, 
#                                                 type_packet, role='SN', action='tx', verbose=VERBOSE)
            
#             print('Energía del SN despues de tx datos : ', sender_id['ResidualEnergy'])
            
#             # energía despues de la trasmisión 
#             energy_consumed_sn += ((initial_energy_sn - sender_id["ResidualEnergy"]))
#             print('Energia consumida por el SN en este proceso : ', energy_consumed_sn)
#             log_transmission_event(sender_id=sender_id['NodeID'], receiver_id=receiver_id['NodeID'], 
#                                    cluster_id=sender_id["ClusterHead"], distance_m=distance, latency_ms=latency_encryp_ms,
#                                    bits_sent=bits_sent, bits_received=bits_sent, packet_lost=p_lost, success=per_data,
#                                    energy_j=energy_consumed_sn, shared_key_id=shared_key_id, msg_type=msg_type)
        
#             # Energia antes de la trasmisión
#             # **Nuevo: Medir energía inicial del CH**
#             initial_energy_ch = receiver_id['ResidualEnergy']
#             print('Energía inicial antes de actualizar el CH : ', initial_energy_ch)
#             # Calcular el timeout de espera
#             lat_prop, lat_tx, lat_proc, timeout = calculate_timeout(start_position, end_position, bitrate=9200, 
#                                                                     packet_size=bits_received)
#             receiver_id = update_energy_node_tdma(receiver_id, sender_id["Position"], E_schedule, timeout, 
#                                                 type_packet, role='CH', action='rx', verbose=VERBOSE)
            
#             # print('Nodo CH : ', receiver_id)

#             print('Energía del CH despues de rx datos : ', receiver_id['ResidualEnergy'])
#             # energía despues de la trasmisión 
#             energy_consumed_ch += ((initial_energy_ch - receiver_id["ResidualEnergy"]))
#             print('Energia consumida por el CH en este proceso :' ,energy_consumed_ch)
#             log_transmission_event(sender_id=sender_id['NodeID'], receiver_id=receiver_id['NodeID'], 
#                                 cluster_id=sender_id["ClusterHead"], distance_m=distance, latency_ms=latency_dec_ms,
#                                     bits_sent=bits_sent, bits_received=bits_received, packet_lost=p_lost, success=per_data,
#                                     energy_j=energy_consumed_ch, shared_key_id=shared_key_id, msg_type=msg_type)
            
#             ack_result = simulate_ack_response(sender_id, receiver_id, E_schedule)

#             if ack_result["ack_success"]:
#                 print("✅ ACK recibido correctamente")
#             else:
#                 print("⚠️ ACK perdido — posible retransmisión")

            
#         elif source == 'CH' and dest == 'Sink':
#             # Energia antes de la trasmisión
#             # **Nuevo: Medir energía inicial del CH**
#             initial_energy = sender_id['ResidualEnergy']
#             print('Energía inicial antes de actualizar : ', initial_energy)
#             # Calcular el timeout de espera
#             lat_prop, lat_tx, lat_proc, timeout = calculate_timeout(start_position, end_position, bitrate=9200, 
#                                                                     packet_size=bits_received)
#             sender_id = update_energy_node_tdma(sender_id, receiver_id["Position"], E_schedule, timeout, 
#                                                 type_packet, role='CH', action='tx', verbose=VERBOSE)
            
#             # energía despues de la trasmisión 
#             energy_consumed_ch += ((initial_energy - sender_id["ResidualEnergy"]))
#             print('Energia consumida por el CH : ', energy_consumed_ch)
#             log_transmission_event(sender_id=sender_id['NodeID'], receiver_id=receiver_id['NodeID'], 
#                                 cluster_id=sender_id["ClusterHead"], distance_m=distance, latency_ms=latency_encryp_ms,
#                                     bits_sent=bits_sent, bits_received=bits_sent, packet_lost=p_lost, success=per_data,
#                                     energy_j=energy_consumed_ch, shared_key_id=shared_key_id, msg_type=msg_type)

#             ack_result = simulate_ack_response(sender_id, receiver_id, E_schedule, sink=True)

#             if ack_result["ack_success"]:
#                 print("✅ ACK recibido correctamente")
#             else:
#                 print("⚠️ ACK perdido — posible retransmisión")

#         # summarize_metrics()
#         # export_metrics_to_json()  # Puedes especificar otro nombre si lo deseas
#         # export_metrics_to_csv()
                                
#     else:
#         print(f"🚨 Error: No se encontró clave compartida entre {sender} y {receiver}")


import numpy as np
import random
import time

# def simulate_ack_response(sender_node, receiver_node, E_schedule, ack_size_bits=72, bitrate=9200, sink=False):
#     # 1. Calcular distancia
#     distance = np.linalg.norm(np.array(sender_node["Position"]) - np.array(receiver_node["Position"]))  # se debe comentar 10/09/2025

#     # 2. Simular retardo de propagación
#     #delay = (propagation_time(distance, receiver_node["Position"], sender_node["Position"]))    # se comenta 10/09/2025
#     delay = (propagation_time1(receiver_node["Position"], sender_node["Position"], depth=None, region="standard"))
#     latencia_ms = delay * 1000  # delay en milisegundos
#     # time.sleep(delay)

#     # 3. Simular pérdida de ACK
#     per_ack, SL_db, snr_db, EbN0_db, ber = per_from_link(f_khz=20.0, distance_m=distance, L=ack_size_bits, bitrate=9200)
#     # ack_lost = random.random() > 0.95  # 5% de pérdida
#     # ack_success = not ack_lost

#     if not per_ack:
#         # p_lost = not success
#         ack_lost = True
#         print("⚠️ Paquete perdido durante la transmisión simulada", ack_lost)
#     else:
#         ack_lost = False

#     # 4. Timeout basado en distancia y tamaño de ACK
#     lat_prop, lat_tx, lat_proc, timeout = calculate_timeout(receiver_node["Position"], sender_node["Position"], 
#                                                             bitrate=bitrate, packet_size=ack_size_bits)

#     # 6. Tiempo estimado del ACK
#     ack_tx_time = (ack_size_bits / bitrate) * 1000
#     total_ack_time_ms = latencia_ms + ack_tx_time

#     # 5. Calcular energía para TX (receptor) y RX (emisor)
#     # ACK va del receptor (CH o Sink) al emisor (SN o CH)
#     if sink == False:
#         receiver_initial_energy = receiver_node["ResidualEnergy"]
#         receiver_node = update_energy_node_tdma(receiver_node, sender_node["Position"], E_schedule, timeout,
#                                                 type_packet="ack", role="ACK_SENDER", action="tx", verbose=VERBOSE)
#         E_tx = receiver_initial_energy - receiver_node["ResidualEnergy"]

#         log_transmission_event(sender_id=receiver_node['NodeID'], receiver_id=sender_node['NodeID'], 
#                                 cluster_id=sender_node["ClusterHead"], distance_m=distance, latency_ms=total_ack_time_ms,
#                                     bits_sent=ack_size_bits, bits_received=ack_size_bits, packet_lost=ack_lost, success=per_ack,
#                                     energy_j=E_tx, shared_key_id=None, msg_type="ACK_SENDER")
#     else:
#         E_tx = 0

#     sender_initial_energy = sender_node["ResidualEnergy"]
#     sender_node = update_energy_node_tdma(sender_node, receiver_node["Position"], E_schedule, timeout,
#                                           type_packet="ack", role="ACK_RECEIVER", action="rx", verbose=VERBOSE)
#     E_rx = sender_initial_energy - sender_node["ResidualEnergy"]

#     log_transmission_event(sender_id=receiver_node['NodeID'], receiver_id=sender_node['NodeID'], 
#                                 cluster_id=sender_node["ClusterHead"], distance_m=distance, latency_ms=total_ack_time_ms,
#                                     bits_sent=ack_size_bits, bits_received=ack_size_bits, packet_lost=ack_lost, success=per_ack,
#                                     energy_j=E_rx, shared_key_id=None, msg_type="ACK_RECEIVER")

   

#     return {
#         # "ack_success": ack_success,
#         "ack_success": per_ack,
#         "ack_lost": ack_lost,
#         "ack_latency_s": total_ack_time_ms,
#         "ack_energy_tx": E_tx,
#         "ack_energy_rx": E_rx,
#         "receiver_node": receiver_node,
#         "sender_node": sender_node
#     }


def transmit_data(RUN_ID, db_path, nodes, sender_node, receiver_node, plaintext, E_schedule,
                  source='SN', dest='CH', bitrate=9200):
    """
    Envío de DATA/AGG entre (SN->CH) y (CH->Sink) con:
    - cifrado ASCON (enc/dec) para medir t_proc,
    - PER por enlace con per_from_link + Bernoulli,
    - energía vía update_energy_node_tdma (incluye t_verif_s),
    - logging canónico con log_event (TX y RX),
    - ACK simulado al final del hop.
    """
    # 0) Tipo de paquete por hop
    if source == 'SN' and dest == 'CH':
        msg_type = type_packet = 'data'
        role_tx, role_rx = 'SN', 'CH'
    elif source == 'CH' and dest == 'Sink':
        msg_type = type_packet = 'agg'
        role_tx, role_rx = 'CH', 'Sink'
    else:
        msg_type = type_packet = 'data'
        role_tx, role_rx = source, dest

    # 1) DB path (en /data/)
    current_dir = os.getcwd()
    carpeta_destino = os.path.join(current_dir, 'data')
    os.makedirs(carpeta_destino, exist_ok=True)
    ruta_bbdd = os.path.join(carpeta_destino, db_path)

    # 2) Obtener clave compartida
    conn = sqlite3.connect(ruta_bbdd)
    cursor = conn.cursor()
    sender_id = int(sender_node["NodeID"])
    receiver_id = int(receiver_node["NodeID"])
    cursor.execute("SELECT shared_key, id FROM shared_keys WHERE node_id = ? AND peer_id = ?", (sender_id, receiver_id))
    row = cursor.fetchone()
    conn.close()

    if not row:
        print(f"🚨 No hay clave compartida entre {sender_id} y {receiver_id}")
        return

    shared_key, shared_key_id = row[0], row[1]

    # 3) Cifrado/Descifrado (para t_proc)
    t0 = time.perf_counter()
    encrypted_msg = encrypt_message(shared_key, plaintext)     # ASCON-128
    t1 = time.perf_counter()
    t_enc_s = t1 - t0

    # print("Mensaje encriptado : ", encrypted_msg.hex(), " time : ", t_enc_s, "tamaño (hex) : ", len(encrypted_msg.hex()))
    # print("Mensaje encriptado : ", encrypted_msg, " time : ", t_enc_s, "tamaño (bin): ", len(encrypted_msg))

    # Nota: aquí solo medimos descifrado local para stats (RX real descifra después)
    t2 = time.perf_counter()
    desencrypted_msg = decrypt_message(shared_key, encrypted_msg)
    t3 = time.perf_counter()
    t_dec_s = t3 - t2

    # print("Mensaje desencriptado : ", desencrypted_msg, " time : ", t_dec_s, len(desencrypted_msg))

    # 4) Geometría + tiempos físicos
    start_pos = np.array(sender_node["Position"])
    end_pos   = np.array(receiver_node["Position"])
    distance  = float(np.linalg.norm(start_pos - end_pos))
    t_prop_s  = float(propagation_time1(start_pos, end_pos, depth=None, region="standard"))
    if source == 'SN':
        bits_sent = int((len(encrypted_msg) * 8) + (10 * 8)) # se suman los bytes del header paquete datos nodos
    else:
        bits_sent = int((len(encrypted_msg) * 8) + (11 * 8)) # se suman los bytes del header paquete agregado

    # print("bits_sent :", bits_sent)
    t_tx_s    = bits_sent / float(bitrate)

    # 5) PER del enlace y Bernoulli
    per_link, SL_db, snr_db, EbN0_db, ber = per_from_link(f_khz=20.0, distance_m=distance, L=bits_sent, bitrate=bitrate)
    success  = propagate_with_probability(per=per_link, override_per=PER_VARIABLE)
    p_lost   = (not success)
    bits_rcv = bits_sent if success else 0

    # 6) Timeout y energía TX (incluye t_proc del emisor = cifrado)
    #    Usamos tu calculate_timeout con proc_time_s=t_enc_s para que el modelo de tiempo sea coherente
    lat_prop_ms, lat_tx_ms, lat_proc_ms, timeout_s = calculate_timeout(start_pos, end_pos, bitrate=bitrate,
                                                                       packet_size=bits_sent, proc_time_s=t_enc_s)
    # E en TX (emisor)
    e0_tx = float(sender_node["ResidualEnergy"])
    sender_node = update_energy_node_tdma(sender_node, end_pos, E_schedule, timeout_s,
                                          type_packet, role=role_tx, action="tx", verbose=VERBOSE,
                                          t_verif_s=t_enc_s)
    E_tx = e0_tx - float(sender_node["ResidualEnergy"])

    # 7) Log TX (emisor)
    log_event(
        run_id=RUN_ID, phase="data", module="ascon", msg_type=f"DATA:{msg_type}:TX",
        sender_id=sender_id, receiver_id=receiver_id, cluster_id=sender_node.get("ClusterHead"),
        start_pos=start_pos, end_pos=end_pos,
        bits_sent=bits_sent, bits_received=bits_rcv, payload_bits=PAYLOAD_BITS_SN if dest == 'CH' else PAYLOAD_BITS_CH,
        success=success, packet_lost=p_lost,
        energy_event_type='tx', energy_j=E_tx,
        residual_sender=sender_node["ResidualEnergy"], residual_receiver=0 if dest == 'Sink' else receiver_node["ResidualEnergy"],
        bitrate=bitrate, freq_khz=20,
        lat_prop_ms=t_prop_s*1000.0, lat_tx_ms=t_tx_s*1000.0, lat_proc_ms=t_enc_s*1000.0,
        # lat_prop_ms=lat_prop_ms, lat_tx_ms=lat_tx_ms, lat_proc_ms=t_enc_s*1000.0,
        snr_db=snr_db, per=per_link, lat_dag_ms=0.0, SL_db=SL_db, EbN0_db=EbN0_db, BER=ber
    )

    # Se actualiza la energia de los demas nodos
    active_ids = [sender_id, receiver_id]
    active_cluster_id = sender_node["ClusterHead"]
    nodes = update_energy_standby_others(nodes, active_ids, active_cluster_id,
                                         timeout_s, verbose=VERBOSE)

    # 8) Si el paquete llega: energía RX (receptor) + descifrado
    if success:
        # Tiempo de proceso en RX (descifrado)
        t_proc_rx_s = t_dec_s

        # Modelo tiempo para RX (proc = t_proc_rx_s)
        _, _, _, timeout_rx_s = calculate_timeout(start_pos, end_pos, bitrate=bitrate,
                                                  packet_size=bits_sent, proc_time_s=t_proc_rx_s)
        if not(dest == 'Sink'):
            # E en RX (receptor)
            e0_rx = float(receiver_node["ResidualEnergy"])
            receiver_node = update_energy_node_tdma(receiver_node, start_pos, E_schedule, timeout_rx_s,
                                                    type_packet, role=role_rx, action="rx", verbose=VERBOSE,
                                                    t_verif_s=t_proc_rx_s)
            E_rx = e0_rx - float(receiver_node["ResidualEnergy"])
        else:
            E_rx = 0

        # 9) Log RX (receptor) Solo consume energia en caso de recibir el paquete
        log_event(
            run_id=RUN_ID, phase="data", module="ascon", msg_type=f"DATA:{msg_type}:RX",
            sender_id=sender_id, receiver_id=receiver_id, cluster_id=receiver_node.get("ClusterHead") if not(dest == 'Sink') else sender_node.get("ClusterHead"),
            start_pos=start_pos, end_pos=end_pos,
            bits_sent=bits_sent, bits_received=bits_rcv, payload_bits=PAYLOAD_BITS_SN if dest == 'CH' else PAYLOAD_BITS_CH,
            success=success, packet_lost=p_lost,
            energy_event_type='rx', energy_j=E_rx,
            residual_sender=sender_node["ResidualEnergy"], residual_receiver=0 if dest == 'Sink' else receiver_node["ResidualEnergy"],
            bitrate=bitrate, freq_khz=20,
            lat_prop_ms=t_prop_s*1000.0, lat_tx_ms=t_tx_s*1000.0, lat_proc_ms=t_proc_rx_s*1000.0,
            snr_db=snr_db, per=per_link, lat_dag_ms=0.0, SL_db=SL_db, EbN0_db=EbN0_db, BER=ber
        )
    else:
        if "ResidualEnergy" in receiver_node:
            # si se pierde, RX no consume por decodificación del paquete (mantén solo listen en update_energy_standby_others externo si quieres)
            receiver_node = update_energy_failed_rx(receiver_node, start_pos, timeout_s, role=role_rx, verbose=VERBOSE)
            E_rx = 0.0
            t_proc_rx_s = 0.0


    # # 9) Log RX (receptor)
    # log_event(
    #     run_id=RUN_ID, phase="data", module="ascon", msg_type=f"DATA:{msg_type}:RX",
    #     sender_id=sender_id, receiver_id=receiver_id, cluster_id=receiver_node.get("ClusterHead"),
    #     start_pos=start_pos, end_pos=end_pos,
    #     bits_sent=bits_sent, bits_received=bits_rcv,
    #     success=success, packet_lost=p_lost,
    #     energy_event_type='rx', energy_j=E_rx,
    #     residual_sender=sender_node["ResidualEnergy"], residual_receiver=0 if dest == 'Sink' else receiver_node["ResidualEnergy"],
    #     bitrate=bitrate, freq_khz=20,
    #     lat_prop_ms=t_prop_s*1000.0, lat_tx_ms=t_tx_s*1000.0, lat_proc_ms=t_proc_rx_s*1000.0,
    #     snr_db=snr_db, per=per_link, lat_dag_ms=0.0, SL_db=SL_db, EbN0_db=EbN0_db, BER=ber
    # )

    # # 10) ACK hop (usa tu simulador; ya hace logging con log_transmission_event, pero mantenemos consistencia)
    # ack = simulate_ack_response(sender_node, receiver_node, E_schedule, ack_size_bits=72, bitrate=bitrate,
    #                             sink=(dest=='Sink'))
    
    return encrypted_msg

import struct

def encode_marine_payload():
    # Rangos típicos
    temp = round(random.uniform(0.0, 30.0), 3)       # °C
    salinity = round(random.uniform(30.0, 40.0), 3)  # PSU
    pressure = round(random.uniform(0.0, 6000.0), 2) # dbar

    # Escalado
    T = int(temp * 1000)       # 3 decimales → uint16
    S = int(salinity * 1000)   # 3 decimales → uint16
    P = int(pressure * 10)     # 1 decimales → uint16 (hasta 6553.5 dbar)

    # Empaquetar en binario
    payload = struct.pack(">HHH", T, S, P)  # 6 bytes

    return payload, (temp, salinity, pressure)


# ######################
# # 📌 Ejemplo de simulación de transmisión:
# transmit_data("bbdd_keys_shared_sign_cipher.db", 16, 402, "Temperatura: 15.2°C")

# # Cargar los nodos del archivo pickle
# import pickle

# # Cargas nodos y sink
# # Para cargar la estructura de nodos guardada
# with open('save_struct/nodos_guardados.pkl', 'rb') as file:
#     node_uw = pickle.load(file)

# # Para cargar la estructura de nodos guardada
# with open('save_struct/sink_guardado.pkl', 'rb') as file:
#     node_sink = pickle.load(file)


# # Identificar Cluster Heads (CH)
# CH = [nodo["NodeID"] for nodo in node_uw if "ClusterHead" in nodo and nodo["ClusterHead"] == nodo["NodeID"]]

# print("Cluster Head : ", CH)

# # Se crea la tabla
# create_shared_keys_table("bbdd_keys_shared_sign_cipher.db")

# print("🚀 Iniciando simulación de red submarina con ID de claves aleatorias...")

# # 📌 Generar claves compartidas después de la autenticación
# generate_shared_keys("bbdd_keys_shared_sign_cipher.db", node_uw, CH, node_sink)

# # 📌 Simulación de transmisión de información entre nodos y CHs
# # for i in range(0, 20):  # Simular 10 envíos
# #     ch_id = node_uw[i]["ClusterHead"]
# #     node_cluster = node_uw[ch_id - 1]
# #     # transmit_data("bbdd_keys_shared_sign_cipher.db", node_uw[i]["NodeID"], ch_id, f"Temperatura: {np.random.uniform(5, 30):.2f}°C")
# #     transmit_data("bbdd_keys_shared_sign_cipher.db", node_uw[i], node_cluster, f"Temperatura: {np.random.uniform(5, 30):.2f}°C")

# import numpy as np

# # Número total de transmisiones que queremos completar
# total_transmissions = 20
# completed_transmissions = 0  # Contador de transmisiones realizadas
# max_attempts = 100  # Para evitar un bucle infinito si no hay nodos elegibles
# attempts = 0

# attempts = 0
# while completed_transmissions < total_transmissions and attempts < max_attempts:
#     attempts += 1  # Contador de intentos para evitar bucles infinitos
    
#     # Seleccionamos un nodo aleatorio
#     sender_index = np.random.randint(0, len(node_uw))  # Selección aleatoria de nodo
#     sender = node_uw[sender_index]

#     # Obtener el ID del Cluster Head (CH)
#     ch_id = sender.get("ClusterHead")

#     # Validar que el nodo tiene un Cluster Head asignado
#     if ch_id is None or ch_id == sender["NodeID"]:
#         continue  # Saltar si el nodo no tiene CH o si es su propio CH

#     # Obtener el nodo Cluster Head
#     receiver = node_uw[ch_id - 1]

#     # Transmitir datos
#     transmit_data("bbdd_keys_shared_sign_cipher.db", sender, receiver, f"Temperatura: {np.random.uniform(5, 30):.2f}°C")

#     completed_transmissions += 1  # Incrementar transmisiones realizadas

# # 📌 Simulación de CH enviando datos al Sink
# for ch in CH:
#     node_cluster = node_uw[ch - 1]
#     transmit_data("bbdd_keys_shared_sign_cipher.db", node_cluster, node_sink, "Datos agregados del cluster")

# print(f"✅ Simulación completa: {completed_transmissions}/{total_transmissions} transmisiones realizadas.")
# #################