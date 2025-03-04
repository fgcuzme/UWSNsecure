#%%
#### BASE DE DATOS SIN CIFRADO
#############################

import sqlite3
from cryptography.hazmat.primitives.asymmetric import ed25519, x25519
from cryptography.hazmat.primitives import serialization
from ascon import encrypt, decrypt
import os

## CIFRADO Y DESCIFRADO DE CLAVES PRIVADAS
def encrypt_private_key(private_key_bytes, key):
    """
    Cifra la clave privada usando Ascon.
    private_key_bytes: La clave privada en formato de bytes.
    key: La clave de cifrado de 16, 20, o 32 bytes.
    """
    nonce = b'\x00' * 16  # Un nonce fijo para simplificar (en producción, usa uno aleatorio y almacénalo junto con el resultado)
    associated_data = b""  # Puedes agregar datos adicionales para la autenticación
    encrypted_key = encrypt(key, nonce, associated_data, private_key_bytes, variant="Ascon-128")
    return encrypted_key

def decrypt_private_key(encrypted_key, key):
    """
    Descifra la clave privada usando Ascon.
    encrypted_key: La clave privada cifrada en formato de bytes.
    key: La clave de cifrado de 16, 20, o 32 bytes.
    """
    nonce = b'\x00' * 16  # Debe coincidir con el nonce usado en el cifrado
    associated_data = b""
    decrypted_key = decrypt(key, nonce, associated_data, encrypted_key, variant="Ascon-128")
    return decrypted_key


# # Genera una clave de cifrado segura
# key = b"0123456789012345"

# # Simula una clave privada
# x25519_private_key = x25519.X25519PrivateKey.generate()
# private_bytes_x25519 = x25519_private_key.private_bytes(
#             encoding=serialization.Encoding.Raw,
#             format=serialization.PrivateFormat.Raw,
#             encryption_algorithm=serialization.NoEncryption()
#         )
# print(f"Clave sin cifrar: {private_bytes_x25519.hex()} -> tamaño {len(private_bytes_x25519)}")

# # Cifra la clave privada
# encrypted_key = encrypt_private_key(private_bytes_x25519, key)
# print(f"Clave cifrada: {encrypted_key.hex()}  -> tamaño {len(private_bytes_x25519)}")

# # Descifra la clave privada
# decrypted_key = decrypt_private_key(encrypted_key, key)
# print(f"Clave descifrada: {decrypted_key.hex()}  -> tamaño {len(private_bytes_x25519)}")

#%%

### GENERACIÓN DE CLAVES PARA GENERAR CLAVE COMPARTIDA X25519

# Función para generar y guardar claves sin cifrado, se crear una TABLA: keys_shared_x25519
def generarte_keys_shared_without_cipher(db_path):
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
    
    # Eliminar la tabla si ya existe
    cursor.execute('''DROP TABLE IF EXISTS keys_shared_x25519''')

    # Crear la tabla, se crea un id para identificador y busqueda en la bbdd
    cursor.execute('''CREATE TABLE IF NOT EXISTS keys_shared_x25519
                      (id INTEGER PRIMARY KEY AUTOINCREMENT, clave_publica BLOB, clave_privada BLOB)''')
    
    for _ in range(1000):
        # Generación de par de claves para establecer clave compartida utilizando X25519
        x25519_private_key = x25519.X25519PrivateKey.generate()
        x25519_public_key = x25519_private_key.public_key()

        # print('Clave Privada guardada : ', x25519_private_key)
        # print('Clave Pública guardada : ', x25519_public_key)

        # Serialización de la clave privada X25519 a formato RAW
        private_bytes_x25519 = x25519_private_key.private_bytes(
            encoding=serialization.Encoding.Raw,
            format=serialization.PrivateFormat.Raw,
            encryption_algorithm=serialization.NoEncryption()
        )

        # print('Clave privada sin cifrar : ', private_bytes_x25519.hex())
        # key = b"1234567890123456"
        # private_bytes_x25519_cipher = encrypt_private_key(private_bytes_x25519, key)
        # print('Clave privada cifrada : ', private_bytes_x25519_cipher.hex())

        # Serialización de la clave pública X25519 a formato RAW
        public_bytes_x25519 = x25519_public_key.public_bytes(
            encoding=serialization.Encoding.Raw,
            format=serialization.PublicFormat.Raw
        )

        # print('Clave Privada guardada : ', private_bytes_x25519)
        # print('Clave Pública guardada : ', public_bytes_x25519)

        # print('tamaño clave privada : ', len(private_bytes_x25519))
        # print('tamaño clave publica : ', len(public_bytes_x25519))

        # Insertar las claves en la base de datos
        cursor.execute("INSERT INTO keys_shared_x25519 (clave_publica, clave_privada) VALUES (?, ?)",
                       (public_bytes_x25519, private_bytes_x25519))

    conn.commit()
    conn.close()

# Crear la base de datos sin cifrado
# generar_claves_sin_cifrado("claves_sin_cifrado.db")
# generarte_keys_shared_without_cipher("bbdd_keys_shared_sign_cipher.db")

#%%
#### Acceder a las Claves de la TABLA keys_shared_x25519
###########################################################
# import sqlite3
# Función para cargar claves sin cifrado desde la base de datos SQLite
def load_keys_shared_withou_cipher(db_path, table_name, index):
    # claves = []
    # Obtener la ruta del directorio donde se encuentra el script actual
    current_dir = os.getcwd()
    # print('Verificar ruta : ', current_dir)
    
    # Definir la carpeta donde se encuentra la base de datos (carpeta 'data')
    carpeta_destino = os.path.join(current_dir, 'data')

    # Ruta completa del archivo de la base de datos dentro de la carpeta 'data'
    ruta_bbdd = os.path.join(carpeta_destino, db_path)

    conn = sqlite3.connect(ruta_bbdd)
    cursor = conn.cursor()
    
    # Buscar la clave pública y privada por su ID
    cursor.execute(f"SELECT clave_publica, clave_privada FROM {table_name} WHERE id = ?", (index,))
    row = cursor.fetchone()
    
    print(row)
    # for row in cursor.fetchall():
    if row:
        clave_publica_bytes, clave_privada_bytes = row

        # print('Clave privada : ', clave_privada_bytes)
        # print('Clave publica : ', clave_publica_bytes)

        # print('tamaño clave recuperada : ', len(clave_privada_bytes))
        # print('tamaño clave publica recuperada : ', len(clave_publica_bytes))
        # key = b"1234567890123456"
        # private_bytes_x25519_plain = encrypt_private_key(clave_privada_bytes, key)
        # print('Tamaño : ', len(private_bytes_x25519_plain))

        conn.close()
        return clave_privada_bytes, clave_publica_bytes
    else:
        conn.close()
        raise ValueError(f"No se encontró la clave con ID {index}")


# # Ejemplo de cómo buscar una clave específica por su ID
# clave_privada, clave_publica = load_keys_shared_withou_cipher("bbdd_keys_shared_sign_cipher.db", "keys_shared_x25519", index=500)
# print('clave privada para shared x25519 : ', clave_privada.hex())
# print('clave pública para shared x25519 : ', clave_publica.hex())
##############################################


#%%# CREAR TABLA keys_sign_ed25519 DE PAR DE CLAVES PARA FIRMAS DE MENSAJES
# Función para generar y guardar claves sin cifrado
def generarte_keys_sign_without_cipher(db_path):
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
    
    # Eliminar la tabla si ya existe
    cursor.execute('''DROP TABLE IF EXISTS keys_sign_ed25519''')

    # Crear la tabla, se crea un id para identificador y busqueda en la bbdd
    cursor.execute('''CREATE TABLE IF NOT EXISTS keys_sign_ed25519
                      (id INTEGER PRIMARY KEY AUTOINCREMENT, clave_publica BLOB, clave_privada BLOB)''')
    
    for _ in range(1000):
        # Generación de par de claves para firmar y verificar mensajes utilizando Ed25519
        ed25519_private_key = ed25519.Ed25519PrivateKey.generate()
        ed25519_public_key = ed25519_private_key.public_key()

        # Serialización de la clave privada X25519 a formato RAW
        private_bytes_ed25519 = ed25519_private_key.private_bytes(
            encoding=serialization.Encoding.Raw,
            format=serialization.PrivateFormat.Raw,
            encryption_algorithm=serialization.NoEncryption()
        )

        # Serialización de la clave pública X25519 a formato RAW
        public_bytes_ed25519 = ed25519_public_key.public_bytes(
            encoding=serialization.Encoding.Raw,
            format=serialization.PublicFormat.Raw
        )

        # print('tamaño clave privada : ', len(private_bytes_ed25519))
        # print('tamaño clave publica : ', len(public_bytes_ed25519))

        # Insertar las claves en la base de datos
        cursor.execute("INSERT INTO keys_sign_ed25519 (clave_publica, clave_privada) VALUES (?, ?)",
                       (public_bytes_ed25519, private_bytes_ed25519))

    conn.commit()
    conn.close()

# Crear la base de datos sin cifrado
# generar_claves_sin_cifrado("claves_sin_cifrado.db")
# generarte_keys_sign_without_cipher("bbdd_keys_shared_sign_cipher.db")

#%%

# Consultar claves para firmar mensajes
#%%
#### Acceder a las Claves de la TABLA keys_shared_x25519
###########################################################
# import sqlite3
# Función para cargar claves sin cifrado desde la base de datos SQLite
def load_keys_sign_withou_cipher(db_path, table_name, index):
    # claves = []
    # Obtener la ruta del directorio donde se encuentra el script actual
    current_dir = os.getcwd()
    # print('Verificar ruta : ', current_dir)
    
    # Definir la carpeta donde se encuentra la base de datos (carpeta 'data')
    carpeta_destino = os.path.join(current_dir, 'data')

    # Ruta completa del archivo de la base de datos dentro de la carpeta 'data'
    ruta_bbdd = os.path.join(carpeta_destino, db_path)

    conn = sqlite3.connect(ruta_bbdd)
    cursor = conn.cursor()
    
    # Buscar la clave pública y privada por su ID
    cursor.execute(f"SELECT clave_publica, clave_privada FROM {table_name} WHERE id = ?", (index,))
    row = cursor.fetchone()
    
    print(row)
    # for row in cursor.fetchall():
    if row:
        clave_publica_bytes, clave_privada_bytes = row

        # print('Clave privada : ', clave_privada_bytes)
        # print('Clave publica : ', clave_publica_bytes)

        # print('tamaño clave recuperada : ', len(clave_privada_bytes))
        # print('tamaño clave publica recuperada : ', len(clave_publica_bytes))

        conn.close()
        return clave_privada_bytes, clave_publica_bytes
    else:
        conn.close()
        raise ValueError(f"No se encontró la clave con ID {index}")


# # Ejemplo de cómo buscar una clave específica por su ID
# clave_privada, clave_publica = load_keys_sign_withou_cipher("bbdd_keys_shared_sign_cipher.db", "keys_sign_ed25519", index=664)
# print('clave privada para firma ed25519 : ', clave_privada.hex())
# print('clave pública para firma ed25519 : ', clave_publica.hex())
##############################################
# %%


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
    
    cursor.execute("INSERT INTO shared_keys (node_id, peer_id, shared_key) VALUES (?, ?, ?)",
                   (node_id, peer_id, shared_key))
    
    conn.commit()
    conn.close()


create_shared_keys_table("bbdd_keys_shared_sign_cipher.db")
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


## Verificar pruebas cargar archivo pickle

# 📌 Definir IDs de los nodos
node_id = 14   # Nodo del clúster
ch_id = 3     # Cluster Head



# Cargar los nodos del archivo pickle
import pickle

# Cargas nodos y sink
# Para cargar la estructura de nodos guardada
with open('save_struct/nodos_guardados.pkl', 'rb') as file:
    node_uw = pickle.load(file)

# Para cargar la estructura de nodos guardada
with open('save_struct/sink_guardado.pkl', 'rb') as file:
    nodo_sink = pickle.load(file)

# # print(nodo_sink)

keys_node = node_uw[node_id]['Id_pair_keys_shared']
keys_ch = node_uw[ch_id]['Id_pair_keys_shared']

print("Nodo : ",node_id,"\nClave publica : ",(node_uw[node_id]['PublicKey_shared']).hex(),"\nClave privada : "
      ,(node_uw[node_id]['PrivateKey_shared']).hex(),"\nIdKeys_node : ", keys_node)
print("Nodo CH : ",ch_id,"\nClave publica : ",(node_uw[ch_id]['PublicKey_shared']).hex(),"\nClave privada : "
      ,(node_uw[ch_id]['PrivateKey_shared']).hex(),"\nIdKeys_ch : ", keys_ch)

# 📌 Obtener claves del nodo y del CH
x_pub_node, x_priv_node = get_x25519_keys("bbdd_keys_shared_sign_cipher.db", keys_node)
x_pub_ch, x_priv_ch = get_x25519_keys("bbdd_keys_shared_sign_cipher.db", keys_ch)

# x_pub_node, x_priv_node = get_x25519_keys("bbdd_keys_shared_sign_cipher.db", '1')
# x_pub_ch, x_priv_ch = get_x25519_keys("bbdd_keys_shared_sign_cipher.db", '2')

print("Node : ", node_id,"\nClave publica node :", x_pub_node.hex(), "\nclave privada node :", x_priv_node.hex())
print("Node CH : ", ch_id,"\nClave publica ch :", x_pub_ch.hex(), "\nclave privada ch :", x_priv_ch.hex())

# 📌 Cada nodo genera su clave compartida de forma independiente
if x_priv_node and x_pub_ch:
    shared_key_node = derive_shared_key(x_priv_node, x_pub_ch)  # Nodo del clúster usa su clave privada y la pública del CH
    store_shared_key("bbdd_keys_shared_sign_cipher.db", node_id, ch_id, shared_key_node)
    print(f"✅ Nodo {node_id} generó clave compartida con CH {ch_id}: {shared_key_node.hex()}")

if x_priv_ch and x_pub_node:
    shared_key_ch = derive_shared_key(x_priv_ch, x_pub_node)  # CH usa su clave privada y la pública del nodo
    store_shared_key("bbdd_keys_shared_sign_cipher.db", ch_id, node_id, shared_key_ch)
    print(f"✅ CH {ch_id} generó clave compartida con nodo {node_id}: {shared_key_ch.hex()}")

# 📌 Verificación
assert shared_key_node == shared_key_ch, "Error: Las claves compartidas no coinciden"
print("🔐 Claves compartidas generadas correctamente y almacenadas en la BBDD.")
