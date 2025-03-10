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