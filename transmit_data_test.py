import sqlite3
import random
from metrics import (log_latency, log_throughput, log_energy, log_packet_result, 
                     get_packet_loss_percentage, summarize_metrics, export_metrics_to_json, export_metrics_to_csv)
from transmission_logger import log_transmission_event
from energia_dinamica import calcular_energia_paquete, energy_listen, energy_standby, calculate_timeout, update_energy_node_tdma
from transmission_summary import summarize_per_node, summarize_global

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
            print(f"⚠️ Nodo {node_id} es un CH...")

            # Obtener claves del nodo y su Cluster Head
            x_pub_node, x_priv_node = get_x25519_keys(db_path, key_id)

            shared_key = derive_shared_key(x_priv_node, x_pub_sink)

            #print("db_path : ", db_path, "node_id : ", node_id, "node_sink[NodeID] : ", node_sink["NodeID"], "shared_key : ", shared_key.hex())
            store_shared_key(db_path, node_id, node_sink["NodeID"], shared_key)
            print(f"🔐 CH {node_id} generó clave compartida con el Sink", shared_key.hex())
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
            print(f"🔐 Nodo {node_id} generó clave compartida con CH {ch_id}", shared_key.hex())

        #if node_id in CH:  # Si el nodo es un CH, genera clave con el Sink
            

from ascon import encrypt, decrypt
import os

def encrypt_message(shared_key, plaintext):
    """Cifra un mensaje con ASCON-128 usando la clave compartida."""
    key = shared_key[:16]  # ASCON-128 requiere 16 bytes de clave
    nonce = os.urandom(16)
    associated_data = b""
    ciphertext = encrypt(key, nonce, associated_data, plaintext.encode(), variant="Ascon-128")
    return nonce + ciphertext

def decrypt_message(shared_key, encrypted_message):
    """Descifra un mensaje con ASCON-128."""
    key = shared_key[:16]
    nonce, ciphertext = encrypted_message[:16], encrypted_message[16:]
    associated_data = b""
    return decrypt(key, nonce, associated_data, ciphertext, variant="Ascon-128").decode()


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


def transmit_data(db_path, sender_id, receiver_id, plaintext, E_schedule, source='SN', dest='CH'):
    # """Simula la transmisión de datos cifrados entre nodos usando claves compartidas almacenadas en la base de datos."""
    # conn = sqlite3.connect(db_path)
    # cursor = conn.cursor()

    if source == 'SN' and dest == 'CH':
        msg_type = type_packet = 'data'
    elif source == 'CH' and dest == 'Sink':
        msg_type = type_packet = 'agg'
    # else:
    #     msg_type = type_packet = 'sync'     # Simula el paquete de ack
    
    energy_consumed_sn = 0
    energy_consumed_ch = 0
    initial_energy_sn = 0
    initial_energy_ch = 0

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

    sender = sender_id["NodeID"]
    receiver = receiver_id["NodeID"]

    #print("Dentro de la función transmit data : ", sender, "-->", receiver)

    # Obtener la clave compartida entre los nodos
    # cursor.execute("SELECT shared_key FROM shared_keys WHERE node_id = ? AND peer_id = ?", (sender_id, receiver_id)) # accede al dato tipo blob
    cursor.execute("SELECT shared_key, id FROM shared_keys WHERE node_id = ? AND peer_id = ?", (int(sender), int(receiver))) # accede al dato tipo int
    row = cursor.fetchone()
    conn.close()

    if row:
        shared_key = row[0]
        shared_key_id = row[1]

        start_time_enc = time.time()
        encrypted_msg = encrypt_message(shared_key, plaintext)
        end_time_enc = time.time()
        time_encryp = end_time_enc - start_time_enc
        print(f"📡 {sender} → {receiver} | 🔐 Cifrado: {encrypted_msg.hex()[:20]}...")
        
        start_time_dec = time.time()
        decrypted_msg = decrypt_message(shared_key, encrypted_msg)
        end_time_dec = time.time()
        time_descryp = end_time_dec - start_time_dec
        print(f"📡 {sender} → {receiver} | 📥 Descifrado: {decrypted_msg}")
        
        # Simulación de retardo en la propagación acústica
        # distance = np.random.uniform(100, 1000)  # Distancia aleatoria entre nodos
        distance = np.linalg.norm(sender_id["Position"] - receiver_id["Position"])  # se debe comentar 10/09/2025
        start_position = sender_id["Position"]
        end_position = receiver_id["Position"]
        #delay = propagation_time(distance, start_position, end_position)    # se comenta 10/09/2025
        delay = propagation_time1(start_position, end_position, depth=None, region="standard")
        print(f"delay of propagation data :  {delay}")
        time.sleep(delay)

        latency_ms = ((end_time_enc - start_time_enc) + delay + (end_time_dec - start_time_dec) + 0.02) * 1000  # en milisegundos
        latency_encryp_ms = ((end_time_enc - start_time_enc) + delay + 0.02) * 1000  # en milisegundos
        latency_dec_ms = ( delay + (end_time_dec - start_time_dec) + 0.02) * 1000  # en milisegundos

        # bits_sent = len(plaintext.encode()) * 8
        bits_sent = len(encrypted_msg) * 8

        bits_received = len(encrypted_msg) * 8
        
        # Simular pérdida de paquetes
        success = random.random() > 0.05  # 95% éxito

        if not success:
            # p_lost = not success
            p_lost = True
            print("⚠️ Paquete perdido durante la transmisión simulada", p_lost)
        else:
            p_lost = False

        if source == 'SN' and dest == 'CH':
            # Energia antes de la trasmisión
            # **Nuevo: Medir energía inicial del CH**
            initial_energy_sn = sender_id['ResidualEnergy']
            print('Energía inicial antes de actualizar el nodo : ', initial_energy_sn)
            # Calcular el timeout de espera
            timeout = calculate_timeout(start_position, end_position, bitrate=9200, packet_size=bits_sent)
            sender_id = update_energy_node_tdma(sender_id, receiver_id["Position"], E_schedule, timeout, 
                                                type_packet, role='SN', action='tx', verbose=True)
            print('Energía del SN despues de tx datos : ', sender_id['ResidualEnergy'])
            # energía despues de la trasmisión 
            energy_consumed_sn += ((initial_energy_sn - sender_id["ResidualEnergy"]))
            print('Energia consumida por el SN en este proceso : ', energy_consumed_sn)
            log_transmission_event(sender_id=sender_id['NodeID'], receiver_id=receiver_id['NodeID'], 
                                   cluster_id=sender_id["ClusterHead"], distance_m=distance, latency_ms=latency_encryp_ms,
                                   bits_sent=bits_sent, bits_received=bits_sent, packet_lost=p_lost, success=success,
                                   energy_j=energy_consumed_sn, shared_key_id=shared_key_id, msg_type=msg_type)
        
            # Energia antes de la trasmisión
            # **Nuevo: Medir energía inicial del CH**
            initial_energy_ch = receiver_id['ResidualEnergy']
            print('Energía inicial antes de actualizar el CH : ', initial_energy_ch)
            # Calcular el timeout de espera
            timeout = calculate_timeout(start_position, end_position, bitrate=9200, packet_size=bits_received)
            receiver_id = update_energy_node_tdma(receiver_id, sender_id["Position"], E_schedule, timeout, 
                                                type_packet, role='CH', action='rx', verbose=True)
            
            # print('Nodo CH : ', receiver_id)

            print('Energía del CH despues de rx datos : ', receiver_id['ResidualEnergy'])
            # energía despues de la trasmisión 
            energy_consumed_ch += ((initial_energy_ch - receiver_id["ResidualEnergy"]))
            print('Energia consumida por el CH en este proceso :' ,energy_consumed_ch)
            log_transmission_event(sender_id=sender_id['NodeID'], receiver_id=receiver_id['NodeID'], 
                                cluster_id=sender_id["ClusterHead"], distance_m=distance, latency_ms=latency_dec_ms,
                                    bits_sent=bits_sent, bits_received=bits_received, packet_lost=p_lost, success=success,
                                    energy_j=energy_consumed_ch, shared_key_id=shared_key_id, msg_type=msg_type)
            
            ack_result = simulate_ack_response(sender_id, receiver_id, E_schedule)

            if ack_result["ack_success"]:
                print("✅ ACK recibido correctamente")
            else:
                print("⚠️ ACK perdido — posible retransmisión")

            
        elif source == 'CH' and dest == 'Sink':
            # Energia antes de la trasmisión
            # **Nuevo: Medir energía inicial del CH**
            initial_energy = sender_id['ResidualEnergy']
            print('Energía inicial antes de actualizar : ', initial_energy)
            # Calcular el timeout de espera
            timeout = calculate_timeout(start_position, end_position, bitrate=9200, packet_size=bits_received)
            sender_id = update_energy_node_tdma(sender_id, receiver_id["Position"], E_schedule, timeout, 
                                                type_packet, role='CH', action='tx', verbose=True)
            
            # energía despues de la trasmisión 
            energy_consumed_ch += ((initial_energy - sender_id["ResidualEnergy"]))
            print('Energia consumida por el CH : ', energy_consumed_ch)
            log_transmission_event(sender_id=sender_id['NodeID'], receiver_id=receiver_id['NodeID'], 
                                cluster_id=sender_id["ClusterHead"], distance_m=distance, latency_ms=latency_encryp_ms,
                                    bits_sent=bits_sent, bits_received=bits_sent, packet_lost=p_lost, success=success,
                                    energy_j=energy_consumed_ch, shared_key_id=shared_key_id, msg_type=msg_type)

            ack_result = simulate_ack_response(sender_id, receiver_id, E_schedule, sink=True)

            if ack_result["ack_success"]:
                print("✅ ACK recibido correctamente")
            else:
                print("⚠️ ACK perdido — posible retransmisión")

        # summarize_metrics()
        # export_metrics_to_json()  # Puedes especificar otro nombre si lo deseas
        # export_metrics_to_csv()
                                
    else:
        print(f"🚨 Error: No se encontró clave compartida entre {sender} y {receiver}")


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



import numpy as np
import random
import time

def simulate_ack_response(sender_node, receiver_node, E_schedule, ack_size_bits=48, bitrate=9200, sink=False):
    # 1. Calcular distancia
    distance = np.linalg.norm(np.array(sender_node["Position"]) - np.array(receiver_node["Position"]))  # se debe comentar 10/09/2025

    # 2. Simular retardo de propagación
    #delay = (propagation_time(distance, receiver_node["Position"], sender_node["Position"]))    # se comenta 10/09/2025
    delay = (propagation_time1(receiver_node["Position"], sender_node["Position"], depth=None, region="standard"))
    latencia_ms = delay * 1000  # delay en milisegundos
    time.sleep(delay)

    # 3. Simular pérdida de ACK
    ack_lost = random.random() > 0.95  # 5% de pérdida
    ack_success = not ack_lost

    # 4. Timeout basado en distancia y tamaño de ACK
    timeout = calculate_timeout(receiver_node["Position"], sender_node["Position"], bitrate=bitrate, packet_size=ack_size_bits)

    # 6. Tiempo estimado del ACK
    ack_tx_time = (ack_size_bits / bitrate) * 1000
    total_ack_time = latencia_ms + ack_tx_time

    # 5. Calcular energía para TX (receptor) y RX (emisor)
    # ACK va del receptor (CH o Sink) al emisor (SN o CH)
    if sink == False:
        receiver_initial_energy = receiver_node["ResidualEnergy"]
        receiver_node = update_energy_node_tdma(receiver_node, sender_node["Position"], E_schedule, timeout,
                                                type_packet="ack", role="ACK_SENDER", action="tx", verbose=True)
        E_tx = receiver_initial_energy - receiver_node["ResidualEnergy"]

        log_transmission_event(sender_id=receiver_node['NodeID'], receiver_id=sender_node['NodeID'], 
                                cluster_id=sender_node["ClusterHead"], distance_m=distance, latency_ms=total_ack_time,
                                    bits_sent=ack_size_bits, bits_received=ack_size_bits, packet_lost=ack_lost, success=ack_success,
                                    energy_j=E_tx, shared_key_id=None, msg_type="ACK_SENDER")
    else:
        E_tx = 0

    sender_initial_energy = sender_node["ResidualEnergy"]
    sender_node = update_energy_node_tdma(sender_node, receiver_node["Position"], E_schedule, timeout,
                                          type_packet="ack", role="ACK_RECEIVER", action="rx", verbose=True)
    E_rx = sender_initial_energy - sender_node["ResidualEnergy"]

    log_transmission_event(sender_id=receiver_node['NodeID'], receiver_id=sender_node['NodeID'], 
                                cluster_id=sender_node["ClusterHead"], distance_m=distance, latency_ms=total_ack_time,
                                    bits_sent=ack_size_bits, bits_received=ack_size_bits, packet_lost=ack_lost, success=ack_success,
                                    energy_j=E_rx, shared_key_id=None, msg_type="ACK_RECEIVER")

   

    return {
        "ack_success": ack_success,
        "ack_lost": ack_lost,
        "ack_latency_s": total_ack_time,
        "ack_energy_tx": E_tx,
        "ack_energy_rx": E_rx,
        "receiver_node": receiver_node,
        "sender_node": sender_node
    }
