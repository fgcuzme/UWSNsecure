import sqlite3

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

def derive_shared_key(x_priv_bytes, peer_x_pub_bytes):
    """Deriva una clave compartida usando X25519."""
    private_key = x25519.X25519PrivateKey.from_private_bytes(x_priv_bytes)
    peer_public_key = x25519.X25519PublicKey.from_public_bytes(peer_x_pub_bytes)
    return private_key.exchange(peer_public_key)

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
                   (node_id, peer_id, shared_key))
    conn.commit()
    conn.close()

def generate_shared_keys(db_path, node_uw, CH, node_sink):
    """Genera claves compartidas considerando los ID aleatorios asignados a cada nodo."""
    for node in node_uw:
        node_id = node["NodeID"]
        key_id = node["Id_pair_keys_shared"]  # ID de clave aleatoria
        ch_id = node["ClusterHead"]
        
        # Obtener claves del nodo y su Cluster Head
        x_pub_node, x_priv_node = get_x25519_keys(db_path, key_id)
        ch_key_id = next(n["Id_pair_keys_shared"] for n in node_uw if n["NodeID"] == ch_id)
        x_pub_ch, _ = get_x25519_keys(db_path, ch_key_id)

        # Obtener claves del Sink (única clave)
        # sink_key_id = node_sink["Id_pair_keys_shared"]
        # x_pub_sink, _ = get_x25519_keys(db_path, sink_key_id)
        x_pub_sink = node_sink["PublicKey_shared"]

        if x_priv_node and x_pub_ch:
            shared_key = derive_shared_key(x_priv_node, x_pub_ch)
            print("db_path : ", db_path, "node_id : ", node_id, "ch_id : ", ch_id, "shared_key : ", shared_key)
            store_shared_key(db_path, node_id, ch_id, shared_key)
            print(f"🔐 Nodo {node_id} generó clave compartida con CH {ch_id}")

        if node_id in CH:  # Si el nodo es un CH, genera clave con el Sink
            shared_key = derive_shared_key(x_priv_node, x_pub_sink)
            print("db_path : ", db_path, "node_id : ", node_id, "node_sink[NodeID] : ", node_sink["NodeID"], "shared_key : ", shared_key)
            store_shared_key(db_path, node_id, node_sink["NodeID"], shared_key)
            print(f"🔐 CH {node_id} generó clave compartida con el Sink")


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

def transmit_data(db_path, sender_id, receiver_id, plaintext):
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
        
    # Obtener la clave compartida entre los nodos
    cursor.execute("SELECT shared_key FROM shared_keys WHERE node_id = ? AND peer_id = ?", (sender_id, receiver_id))
    row = cursor.fetchone()
    conn.close()

    if row:
        shared_key = row[0]
        encrypted_msg = encrypt_message(shared_key, plaintext)
        
        # Simulación de retardo en la propagación acústica
        distance = np.random.uniform(100, 1000)  # Distancia aleatoria entre nodos
        delay = distance / 1500  # Velocidad del sonido en agua ~1500 m/s
        time.sleep(delay)

        decrypted_msg = decrypt_message(shared_key, encrypted_msg)
        print(f"📡 {sender_id} → {receiver_id} | 🔐 Cifrado: {encrypted_msg.hex()[:20]}... | 📥 Descifrado: {decrypted_msg}")
    else:
        print(f"🚨 Error: No se encontró clave compartida entre {sender_id} y {receiver_id}")

# # 📌 Ejemplo de simulación de transmisión:
# transmit_data("bbdd_keys_shared_sign_cipher.db", 16, 402, "Temperatura: 15.2°C")

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

print("Cluster Head : ", CH)

# Se crea la tabla
create_shared_keys_table("bbdd_keys_shared_sign_cipher.db")

print("🚀 Iniciando simulación de red submarina con ID de claves aleatorias...")

# 📌 Generar claves compartidas después de la autenticación
generate_shared_keys("bbdd_keys_shared_sign_cipher.db", node_uw, CH, node_sink)

# 📌 Simulación de transmisión de información entre nodos y CHs
for i in range(1, 11):  # Simular 10 envíos
    ch_id = node_uw[i]["ClusterHead"]
    transmit_data("bbdd_keys_shared_sign_cipher.db", node_uw[i]["NodeID"], ch_id, f"Temperatura: {np.random.uniform(5, 30):.2f}°C")

# 📌 Simulación de CH enviando datos al Sink
for ch in CH:
    transmit_data("bbdd_keys_shared_sign_cipher.db", ch, node_sink["NodeID"], "Datos agregados del cluster")
