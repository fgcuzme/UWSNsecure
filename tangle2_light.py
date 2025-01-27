from cryptography.hazmat.primitives.asymmetric import ed25519, x25519
from cryptography.hazmat.primitives import hashes, serialization
import time
import random
import ascon


# Función para verificar la firma de una transacción
def verify_transaction_signature(transaction_data, signature, public_key_bytes):
    """
    ed25519
    Verifica la firma de una transacción usando la clave pública.

    transaction_data: Datos de la transacción (string o numérico).
    signature: Firma digital de la transacción (byte array).
    public_key_bytes: Clave pública en formato RAW, DER o PEM (byte array).

    Retorna:
    True si la firma es válida, False si no lo es.
    """
    # Convertir el transaction_id a bytes
    if isinstance(transaction_data, int):  # Si es un número, convertir a string
        transaction_bytes = str(transaction_data).encode('utf-8')
    else:
        # Si ya es un string, convertirlo a bytes
        transaction_bytes = transaction_data.encode('utf-8')


    # verificar si la clave privada ya es un objeto Ed25519PublicKey
    if isinstance(public_key_bytes, ed25519.Ed25519PublicKey):
        actual_pulic_key = public_key_bytes
    else:
        # Cargar la clave pública desde los bytes
        actual_pulic_key = ed25519.Ed25519PublicKey.from_public_bytes(public_key_bytes)
    
    # Verificar la firma

    try:
        actual_pulic_key.verify(signature, transaction_bytes)
        return True  # La firma es válida
    except:
        return False  # La verificación falló



# Función para firmar una transacción con la clave privada
def sign_transaction(transaction_id, private_key_bytes):
    """
    Firma una transacción usando la clave privada en formato DER.

    transaction_id: ID único de la transacción (string).
    private_key_bytes: Clave privada en formato RAW (byte array).

    Retorna:
    Firma digital generada para la transacción (byte array).
    """

    # Convertir el transaction_id a bytes
    if isinstance(transaction_id, int):  # Si es un número, convertir a string
        transaction_bytes = str(transaction_id).encode('utf-8')
    else:
        # Si ya es un string, convertirlo a bytes
        transaction_bytes = transaction_id.encode('utf-8')

    # verificar si la clave privada ya es un objeto Ed25519PrivateKey
    if isinstance(private_key_bytes, ed25519.Ed25519PrivateKey):
        actual_private_key = private_key_bytes
    else:
        # Cargar la clave privada desde los bytes
        actual_private_key = ed25519.Ed25519PrivateKey.from_private_bytes(private_key_bytes)

    print('Clave privada usada : ', actual_private_key)

    # private_key_byte_ed25519 = private_key.private_bytes_raw()
    # print('Clave privada combertida a raw : ', private_key_byte_ed25519.hex())

    # Firmar la transacción usando ed25519
    signature = actual_private_key.sign(transaction_bytes)

    return signature


# # PRUEBAS
# from bbdd2_sqlite3 import load_keys_sign_withou_cipher
# ed25519_private_key, ed25519_public_key = load_keys_sign_withou_cipher("bbdd_keys_shared_sign_cipher.db", "keys_sign_ed25519", index=664)

# # print('Clave privada recuperada : ', ed25519_private_key.hex())
# # print('Clave publica recuperada : ', ed25519_public_key.hex())

# # # Generación de par de claves para firmar y verificar mensajes utilizando Ed25519
# # ed25519_private_key = ed25519.Ed25519PrivateKey.generate()
# # ed25519_public_key = ed25519_private_key.public_key()

# # Mensaje a firmar
# message = b"2c369fbdb9a124037aa7ad053b583a366470b825fa40131a57b544d2b744c846"

# signature1 = sign_transaction(message, ed25519_private_key)
# print('Firma con ed25519 : ', signature1.hex(), ' -> Tamaño : ', len(signature1))

# verifysignature1 = verify_transaction_signature(message, signature1, ed25519_public_key)
# print('Firma con ed25519 : ', verifysignature1)

# # # Ejemplo de uso
# # from bbdd_sqlite3 import load_keys_withou_cipher
# # transaction_id = "tx12345"

# # # Ejemplo de cómo buscar una clave específica por su ID
# # clave_privada, clave_publica = load_keys_withou_cipher("claves_sin_cifrado.db", index=2)

# # # Firmar la transacción
# # signature = sign_transaction(transaction_id, clave_privada)
# # print(f"Firma digital: {signature.hex()} -> Tamaño : {len(signature)}")



# Función para generar un ID único usando Ascon o un hash alternativo
def generate_unique_id_asconhash(node_id):
    """
    Genera un ID único para una transacción usando un hash (Ascon o SHA-256).

    node_id: ID del nodo que genera la transacción.
    Retorna: ID único de la transacción (hash).
    """
    # Obtener la marca de tiempo actual en segundos
    timestamp = str(int(time.time()))
    # # VAriante Obtener la marca de tiempo actual en milisegundos
    # timestamp = str(int(time.time() * 1000))

    # Generar un número aleatorio para asegurar unicidad
    # random_value = str(random.randint(1, 1e9))
    # # Variante Generar un número aleatorio más pequeño
    random_value = str(random.randint(1, 1e6))

    # Concatenar el node_id, timestamp y random_value para crear el identificador de datos
    data = f'{node_id}_{timestamp}_{random_value}'.encode('utf-8')

    # Verifica que el tercer parámetro (longitud del hash) sea entero (si lo necesitas en Ascon)
    hash_length = 32 # Ejemplo de longitud de hash de 32 bytes

    # Usando hashlib como alternativa si no tienes Ascon
    # Si tienes la implementación de Ascon, puedes cambiar hashlib por ascon.hash
    # ascon_hash = ascon.hash(py.bytes(data), 'Ascon-Hash', hash_length)  # Ejemplo con Ascon
    # digest1 = hashlib.sha256(data).hexdigest()  # Usamos SHA-256 en este ejemplo
    digest = ascon.hash(data, "Ascon-Hash", hash_length).hex()

    # print('Hash Firma : ', digest, ' -> Tamaño del Hash', len(digest))

    # Retornar el ID único de la transacción
    return digest

# # Ejemplo de uso
# node_id = 1
# transaction_id = generate_unique_id_asconhash(node_id)
# print(f'Transaction ID: {transaction_id}')

# generate_unique_id_asconhash(1)

# Función para crear una transacción en el Tangle
def create_transaction(node_id, payload, transaction_type, approvedtips, private_key):
    """
    Crear una transacción en el Tangle.

    node_id: ID del nodo que genera la transacción.
    payload: Datos de la transacción (pueden ser datos de sensores o sincronización).
    transaction_type: Tipo de transacción ('Data = 2', 'Sync = 0', 'Control', etc.).
    approved_tips: IDs de las transacciones que esta transacción aprueba.
    private_key: Clave privada del nodo para firmar la transacción.

    Retorna:
    Una estructura de la transacción generada.
    """
    # Crear un ID único para la transacción
    transaction_id = generate_unique_id_asconhash(node_id)

    print('Tx que se aprueban : ', approvedtips)

    # Crear la transacción con sus campos
    transaction = {
        "ID": transaction_id,                # ID único de la transacción -> 32 bytes
        "Timestamp": time.time(),            # Marca de tiempo en segundos -> 2 bytes
        "Source": node_id,                   # Nodo que genera la transacción -> 2 bytes -> si son menos de 255 nodos puede ser un byte
        # "Type": transaction_type,            # Tipo de transacción: 'Data', 'Sync', etc. -> 1 bytes
        "Payload": payload,                  # Datos a transmitir -> 32-64 bytes
        "ApprovedTx": approvedtips,        # Lista de transacciones aprobadas por esta transacción -> 64 bytes
        # "Weight": 1.0,                       # Peso inicial de la transacción -> Eliminar
        # "TipSelectionCount": 0,              # Contador de veces seleccionada como tip -> Eliminar
        "Signature": sign_transaction(transaction_id, private_key)  # Firma con clave privada -> 32 bytes 
    }
    
    return transaction

# TAMAÑO TX -> 32 + 2 + 2 + 64 + 64 + 32 = 196 bytes = 1568 bits
# TAMAÑO TX -> 32 + 2 + 2 + 64 + 64 + 20 = 184 bytes = 1472 bits


# Función para crear el bloque génesis
def create_gen_block(sink_id, private_key):
    """
    Crear el bloque génesis.
    sink_id: ID del Sink (nodo coordinador).
    private_key: Clave privada del Sink para firmar el bloque génesis.
    """

    # # Cargar la clave pública del sink desde los bytes
    # public_key_ed25519 = ed25519.Ed25519PrivateKey.from_private_bytes(private_key)

    # private_key_bytes = public_key_ed25519.private_bytes(
    #     encoding=serialization.Encoding.Raw,
    #     format=serialization.PrivateFormat.Raw,
    #     encryption_algorithm=serialization.NoEncryption()
    # )

    # print('Clave del sink dentro de la función crear Tx genesis: ', private_key_bytes)

    # No se aprueba ninguna transacción, ya que es el primer bloque
    approved_tips = []

    print('Antes de entrar a la función crear Tx... ')

    # Crear la transacción génesis
    genesis_block = create_transaction(sink_id, 'AUTH-REQUEST = 1 -> Génesis de la red', '1', approved_tips, private_key)

    # Agrega la Tx a la lista
    

    # Mostrar mensaje
    # print(f'Bloque génesis creado con ID: {genesis_block["ID"]}')

    return genesis_block


# BORRAR TANGLE EN PYTHON
def delete_tangle(nodo_sink, node_uw, CH):
    # Limpiar los datos del Sink
    nodo_sink['Tips'] = []
    nodo_sink['ApprovedTransactions'] = []
    nodo_sink['Transactions'] = []

    # Restablecer el estado de autenticación en nodo_sink
    for i in range(len(nodo_sink['RegisterNodes'])):
        # nodo_sink['RegisterNodes'][i]['Status_syn'] = False
        nodo_sink['RegisterNodes'][i]['Status_auth'] = False

    # Limpiar los datos de cada nodo en node_uw
    for node in node_uw:
        node['Tips'] = []
        node['ApprovedTransactions'] = []
        node['Transactions'] = []
        node['Authenticated'] = False
        node['ExclusionStatus'] = False

    # Restablecer el estado de autenticación de cada nodo CH
    for ch_index in CH:
        for i in range(len(node_uw[ch_index]['RegisterNodes'])):
            # node_uw[ch_index]['RegisterNodes'][i]['Status_syn'] = False
            node_uw[ch_index]['RegisterNodes'][i]['Status_auth'] = False

    print('Tangle de cada nodo eliminado ...')



# %%
