import time
import numpy as np

import sqlite3
from cryptography.hazmat.primitives.asymmetric import x25519
from ascon import encrypt, decrypt
import os
from bbdd2_sqlite3 import load_keys_shared_withou_cipher, load_keys_sign_withou_cipher


# función que carga las claves X25519 desde la tabla keys_shared_x25519
def get_x25519_keys(db_path, node_id):

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

    """
    Recupera la clave pública y privada de X25519 desde la BBDD según el ID del nodo.
    """
    # conn = sqlite3.connect(db_path)
    # cursor = conn.cursor()
    
    cursor.execute("SELECT clave_publica, clave_privada FROM keys_shared_x25519 WHERE id = ?", (node_id,))
    row = cursor.fetchone()
    
    conn.close()
    
    if row:
        return row[0], row[1]  # Devuelve clave pública y privada en bytes
    return None, None


# x_pub_node, x_priv_node = get_x25519_keys("bbdd_keys_shared_sign_cipher.db", node_id=1)
# print("Clave publica :", x_pub_node.hex(), "\nclave privada :", x_priv_node.hex())


def derive_shared_key(x_priv_bytes, peer_x_pub_bytes):
    """
    Deriva una clave compartida usando el esquema de intercambio de claves X25519.
    """
    # Convertir bytes a objetos clave
    private_key = x25519.X25519PrivateKey.from_private_bytes(x_priv_bytes)
    peer_public_key = x25519.X25519PublicKey.from_public_bytes(peer_x_pub_bytes)

    # Generar la clave compartida
    shared_key = private_key.exchange(peer_public_key)

    return shared_key

# x_pub_ch, _ = get_x25519_keys("bbdd_keys_shared_sign_cipher.db", node_id=2)  # Obtener clave pública del Cluster Head
# shared_key = derive_shared_key(x_priv_node, x_pub_ch)
# print(f"Clave compartida generada: {shared_key.hex()}")


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
    
    cursor.execute('''CREATE TABLE IF NOT EXISTS shared_keys (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        node_id INTEGER,
                        peer_id INTEGER,
                        shared_key BLOB,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')

    conn.commit()
    conn.close()


def store_shared_key(db_path, node_id, peer_id, shared_key):
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
    
    # # Eliminar la tabla si ya existe
    # cursor.execute('''DROP TABLE IF EXISTS keys_shared_x25519''')
    
    # conn = sqlite3.connect(db_path)
    # cursor = conn.cursor()
    
    cursor.execute("INSERT INTO shared_keys (node_id, peer_id, shared_key) VALUES ( ?, ?, ?)",
                   (int(node_id), int(peer_id), shared_key))
    
    conn.commit()
    conn.close()


# create_shared_keys_table("bbdd_keys_shared_sign_cipher.db")
# store_shared_key("bbdd_keys_shared_sign_cipher.db", node_id=90, peer_id=9, shared_key=shared_key)
# print("Clave compartida almacenada correctamente")


# # 1. Obtener claves del nodo y del Cluster Head
# x_pub_node, x_priv_node = get_x25519_keys("bbdd_keys_shared_sign_cipher.db", node_id=100)
# x_pub_ch, _ = get_x25519_keys("bbdd_keys_shared_sign_cipher.db", node_id=200)

# # 2. Generar la clave compartida
# if x_priv_node and x_pub_ch:
#     shared_key = derive_shared_key(x_priv_node, x_pub_ch)
    
#     # 3. Guardar la clave en la BBDD
#     create_shared_keys_table("bbdd_keys_shared_sign_cipher.db")
#     store_shared_key("bbdd_keys_shared_sign_cipher.db", node_id=1, peer_id=2, shared_key=shared_key)
    
#     print(f"Clave compartida almacenada: {shared_key.hex()}")
# else:
#     print("Error: No se encontraron claves válidas en la base de datos")


# ## Verificar pruebas cargar archivo pickle

# # 📌 Definir IDs de los nodos
# node_id = 14   # Nodo del clúster
# ch_id = 3     # Cluster Head


# # # print(nodo_sink)

# keys_node = node_uw[node_id]['Id_pair_keys_shared']
# keys_ch = node_uw[ch_id]['Id_pair_keys_shared']

# print("Nodo : ",node_id,"\nClave publica : ",(node_uw[node_id]['PublicKey_shared']).hex(),"\nClave privada : "
#       ,(node_uw[node_id]['PrivateKey_shared']).hex(),"\nIdKeys_node : ", keys_node)
# print("Nodo CH : ",ch_id,"\nClave publica : ",(node_uw[ch_id]['PublicKey_shared']).hex(),"\nClave privada : "
#       ,(node_uw[ch_id]['PrivateKey_shared']).hex(),"\nIdKeys_ch : ", keys_ch)

# # 📌 Obtener claves del nodo y del CH
# x_pub_node, x_priv_node = get_x25519_keys("bbdd_keys_shared_sign_cipher.db", keys_node)
# x_pub_ch, x_priv_ch = get_x25519_keys("bbdd_keys_shared_sign_cipher.db", keys_ch)

# # x_pub_node, x_priv_node = get_x25519_keys("bbdd_keys_shared_sign_cipher.db", '1')
# # x_pub_ch, x_priv_ch = get_x25519_keys("bbdd_keys_shared_sign_cipher.db", '2')

# print("Node : ", node_id,"\nClave publica node :", x_pub_node.hex(), "\nclave privada node :", x_priv_node.hex())
# print("Node CH : ", ch_id,"\nClave publica ch :", x_pub_ch.hex(), "\nclave privada ch :", x_priv_ch.hex())

# # 📌 Cada nodo genera su clave compartida de forma independiente
# if x_priv_node and x_pub_ch:
#     shared_key_node = derive_shared_key(x_priv_node, x_pub_ch)  # Nodo del clúster usa su clave privada y la pública del CH
#     store_shared_key("bbdd_keys_shared_sign_cipher.db", node_id, ch_id, shared_key_node)
#     print(f"✅ Nodo {node_id} generó clave compartida con CH {ch_id}: {shared_key_node.hex()}")

# if x_priv_ch and x_pub_node:
#     shared_key_ch = derive_shared_key(x_priv_ch, x_pub_node)  # CH usa su clave privada y la pública del nodo
#     store_shared_key("bbdd_keys_shared_sign_cipher.db", ch_id, node_id, shared_key_ch)
#     print(f"✅ CH {ch_id} generó clave compartida con nodo {node_id}: {shared_key_ch.hex()}")

# # 📌 Verificación
# assert shared_key_node == shared_key_ch, "Error: Las claves compartidas no coinciden"
# print("🔐 Claves compartidas generadas correctamente y almacenadas en la BBDD.")


# ####

# función que carga las claves compartidas
def get_x25519_shared_keys(db_path, node_id):

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

    """
    Recupera la clave pública y privada de X25519 desde la BBDD según el ID del nodo.
    """
    # conn = sqlite3.connect(db_path)
    # cursor = conn.cursor()
    
    cursor.execute("SELECT node_id, peer_id, shared_key FROM shared_keys WHERE node_id = ?", (node_id,))
    row = cursor.fetchone()
    
    conn.close()
    
    if row:
        return row[1], row[2]  # Devuelve clave pública y privada en bytes
    return None, None

###

def encrypt_message(shared_key, plaintext):
    """Cifra un mensaje con ASCON usando la clave compartida."""
    nonce = os.urandom(16)
    associated_data = b""
    ciphertext = encrypt(shared_key[:16], nonce, associated_data, plaintext.encode(), variant="Ascon-128")
    #encrypted_key = encrypt(key, nonce, associated_data, private_key_bytes, variant="Ascon-128")
    # print("Mensaje cifrado : ", ciphertext.hex())
    # print("Nonce : ", nonce.hex())
    return nonce + ciphertext  # Incluye el nonce en el mensaje cifrado

def decrypt_message(shared_key, encrypted_message):
    """Descifra un mensaje con ASCON."""
    # print("Separar el nonce : ", encrypted_message[:16])
    # print("Separar el mensaje : ", encrypted_message[16:])
    nonce, ciphertext = encrypted_message[:16], encrypted_message[16:]
    associated_data = b""
    #decrypted_key = decrypt(key, nonce, associated_data, encrypted_key, variant="Ascon-128")
    return decrypt(shared_key[:16], nonce, associated_data, ciphertext, variant="Ascon-128").decode()


# ## Prueba datos de sensores
# from data_sensors import *

# data = generate_sensor_data(f"node_{node_id}")
# plaintext = str(data)
# print("Dato a encriptar : ", plaintext)

# # Simulación de transmisión de datos cifrados
# # plaintext = "Mensaje secreto del nodo al CH tiene este tammaño de dato"
# _, shared_key = get_x25519_shared_keys("bbdd_keys_shared_sign_cipher.db", ch_id)  # Obtener clave compartida del nodo

# print("Clave compartida recuperada : ", shared_key.hex())

# encrypted_msg = encrypt_message(shared_key, plaintext)
# print(f"📤 Mensaje cifrado enviado: {encrypted_msg.hex()}")

# # CH descifra el mensaje
# decrypted_msg = decrypt_message(shared_key, encrypted_msg)
# print(f"📥 Mensaje descifrado en CH: {decrypted_msg}")

def generate_shared_keys(db_path, node_uw, CH, node_sink):
    """Genera claves compartidas considerando los ID aleatorios asignados a cada nodo."""
    for node in node_uw:
        node_id = node["NodeID"]
        key_id = node["Id_pair_keys_shared"]  # ID de clave aleatoria en la BBDD
        ch_id = node["ClusterHead"]

        # Obtener claves del nodo y su Cluster Head
        x_pub_node, x_priv_node = get_x25519_keys(db_path, key_id)
        ch_key_id = next(n["Id_pair_keys_shared"] for n in node_uw if n["NodeID"] == ch_id)
        x_pub_ch, _ = get_x25519_keys(db_path, ch_key_id)

        # 📌 Obtener claves del Sink (Se usa directamente la clave almacenada en node_sink)
        x_pub_sink = node_sink["PublicKey_shared"]  # Convertir la clave del Sink a bytes

        if x_priv_node and x_pub_ch:
            shared_key = derive_shared_key(x_priv_node, x_pub_ch)
            store_shared_key(db_path, node_id, ch_id, shared_key)
            print(f"🔐 Nodo {node_id} generó clave compartida con CH {ch_id}")
            print("shared_key : ", shared_key.hex())

        if node_id in CH:  # Si el nodo es un CH, genera clave con el Sink
            shared_key = derive_shared_key(x_priv_node, x_pub_sink)
            store_shared_key(db_path, node_id, node_sink["NodeID"], shared_key)
            print(f"🔐 CH {node_id} generó clave compartida con el Sink")
            print("shared_key : ", shared_key.hex())


def transmit_data(db_path, sender_id, receiver_id, plaintext, node_sink, node_uw):
    # """Simula la transmisión de datos cifrados entre nodos usando claves compartidas almacenadas en la base de datos."""
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

    # Obtener clave compartida entre nodos dentro de la BBDD
    # cursor.execute("SELECT shared_key FROM shared_keys WHERE node_id = ? AND peer_id = ?", (sender_id, receiver_id)) # accede al dato tipo blob
    cursor.execute("SELECT shared_key FROM shared_keys WHERE node_id = ? AND peer_id = ?", (int(sender_id), int(receiver_id))) # accede al dato tipo int
    row = cursor.fetchone()
    conn.close()

    print("sender_id : ", sender_id, " -> ", "receiver_id : ", receiver_id)

    # 📌 Caso especial: Si el receptor es el Sink, usa la clave almacenada en node_sink
    if receiver_id == node_sink["NodeID"]:
        print(f"🔹 Enviando datos al Sink desde {sender_id}")
        x_pub_receiver = node_sink["PublicKey_shared"] #.encode()  # Convertir clave a bytes
        # x_priv_sender, _ = get_x25519_keys(db_path, sender_id)  # Obtener clave privada del remitente
        x_priv_sender = node_uw[sender_id-1]["PrivateKey_shared"]

        print("Clave publica receptor : ", x_pub_receiver.hex())
        print("Clave privada emisor : ",x_priv_sender.hex())
        
        if x_priv_sender and x_pub_receiver:
            shared_key = derive_shared_key(x_priv_sender, x_pub_receiver)  # Generar clave compartida
        else:
            print(f"🚨 Error al generar clave compartida entre {sender_id} y Sink")
            return
    else:
        # # Obtener clave compartida entre nodos dentro de la BBDD
        # cursor.execute("SELECT shared_key FROM shared_keys WHERE node_id = ? AND peer_id = ?", (sender_id, receiver_id))
        # row = cursor.fetchone()
        # conn.close()

        if row:
            shared_key = row[0]
        else:
            print(f"🚨 Error: No se encontró clave compartida entre {sender_id} y {receiver_id}")
            return

    encrypted_msg = encrypt_message(shared_key, plaintext)

    # Simulación de retardo en la propagación acústica
    distance = np.random.uniform(100, 1000)  # Distancia aleatoria entre nodos
    delay = distance / 1500  # Velocidad del sonido en agua ~1500 m/s
    time.sleep(delay)

    decrypted_msg = decrypt_message(shared_key, encrypted_msg)
    print(f"📡 {sender_id} → {receiver_id} | 🔐 Cifrado: {encrypted_msg.hex()[:20]}... | 📥 Descifrado: {decrypted_msg}")


# Se crea la tabla
create_shared_keys_table("bbdd_keys_shared_sign_cipher.db")

# # 📌 Ejemplo de simulación de transmisión:
# transmit_data("bbdd_keys_shared_sign_cipher.db", 1, 2, "Temperatura: 15.2°C")

# Cargar los nodos del archivo pickle
import pickle

# Cargas nodos y sink
# Para cargar la estructura de nodos guardada
with open('save_struct/nodos_guardados.pkl', 'rb') as file:
    node_uw = pickle.load(file)

# Para cargar la estructura de nodos guardada
with open('save_struct/sink_guardado.pkl', 'rb') as file:
    node_sink = pickle.load(file)

# Identificar Cluster Heads (CH)
CH = [nodo["NodeID"] for nodo in node_uw if "ClusterHead" in nodo and nodo["ClusterHead"] == nodo["NodeID"]]

print("🚀 Iniciando simulación de red submarina con una única BBDD...")

# 📌 Generar claves compartidas después de la autenticación
generate_shared_keys("bbdd_keys_shared_sign_cipher.db", node_uw, CH, node_sink)

# 📌 Simulación de transmisión de información entre nodos y CHs
for i in range(1, 11):  # Simular 10 envíos
    ch_id = node_uw[i]["ClusterHead"]
    transmit_data("bbdd_keys_shared_sign_cipher.db", node_uw[i]["NodeID"], ch_id, f"Temperatura: {np.random.uniform(5, 30):.2f}°C", node_sink, node_uw)

# 📌 Simulación de CH enviando datos al Sink
for ch in CH:
    transmit_data("bbdd_keys_shared_sign_cipher.db", ch, node_sink["NodeID"], "Datos agregados del cluster", node_sink, node_uw)
