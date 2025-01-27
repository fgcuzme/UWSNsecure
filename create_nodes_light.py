import numpy as np
from datetime import datetime
from cryptography.hazmat.primitives.asymmetric import ec, ed25519, x25519
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes, serialization
from bbdd2_sqlite3 import load_keys_shared_withou_cipher, load_keys_sign_withou_cipher

# Función para crear el Sink (equivalente a createSink en MATLAB)
# Función para crear el nodo Sink con su estructura específica
# Función para crear el nodo Sink con su estructura específica
def create_sink(node_id, position, private_key_sign, public_key_sign, private_key_shared, public_key_shared):
    sink = {
        "NodeID": np.uint16(node_id),  # Identificador único del Sink (2 bytes)
        "Position": np.array(position, dtype=np.float32),  # [x, y, z] (12 bytes en total)
        "PrivateKey_sign": private_key_sign,  # Clave privada para firmas(256 bits = 32 bytes)
        "PublicKey_sign": public_key_sign,  # Clave pública para firmas (256 bits = 32 bytes)
        "PrivateKey_shared": private_key_shared,  # Clave privada para secreto compartido(256 bits = 32 bytes)
        "PublicKey_shared": public_key_shared,  # Clave pública para secreto compartido (256 bits = 32 bytes)
        # "Ledger": np.zeros((0, 32), dtype=np.uint8),  # Libro mayor (array de hashes de 256 bits)
        # "SharedKey": np.zeros(32, dtype=np.uint8),  # Clave compartida (256 bits = 32 bytes)
        "NeighborCHs": np.array([], dtype=np.uint16),  # Lista de Cluster Heads cercanos (2 bytes)
        "Timestamp": datetime.now(),  # Marca de tiempo actual del Sink o CH
        # "ApprovedTips": np.zeros((0, 32), dtype=np.uint8),  # Lista de tips aprobados
        # "Weight": np.float32(0),  # Peso acumulado del nodo (según el trabajo realizado)
        "Tips": [],  # Almacena los tips de transacciones no aprobadas
        "ApprovedTransactions": [],  # Transacciones aprobadas por este nodo
        "Transactions": [],  # Transacciones generadas por este nodo
        # Lista de claves públicas de los nodos registrados en la red
        # El campo 'Status' almacenará información sobre si el nodo está autenticado o excluido
        "RegisterNodes": []  # Estructura con NodeID y Status (IsSyn or IsAuth)
    }
    return sink  

# Función para crear un nodo que puede ser Sensor o Cluster Head
def create_node(node_id, position, energy, id_key_sign, private_key_sign, public_key_sign, 
                id_key_shared, private_key_shared, public_key_shared, public_key_sign_sink, public_key_shared_sink):
    node = {
        "NodeID": np.uint16(node_id),  # ID del nodo (2 bytes)
        "Role": np.uint8(0),  # Rol del nodo: CH = 1 o SN = 2 (1 byte)
        "Position": np.array(position, dtype=np.float32),  # [x, y, z] (12 bytes)
        "ResidualEnergy": np.float32(energy),  # Energía residual del nodo (4 bytes)

        # Setear par claves par firmas
        "Id_pair_keys_sign": id_key_sign,
        "PrivateKey_sign": private_key_sign,  # Clave privada (256 bits = 32 bytes)
        "PublicKey_sign": public_key_sign,  # Clave pública (256 bits = 32 bytes)
        
        #Setear par claves para secreto compartido
        "Id_pair_keys_shared": id_key_shared,
        "PrivateKey_shared": private_key_shared,  # Clave privada (256 bits = 32 bytes)
        "PublicKey_shared": public_key_shared,  # Clave pública (256 bits = 32 bytes)

        "ClusterHead": np.uint16([]),  # Referencia al CH si es un nodo sensor (2 bytes)
        "NumCluster": np.uint8([]),  # ID del número de clúster (1 byte)
        "NeighborNodes": np.uint16([]),  # Vecinos (Tips potenciales para aprobar transacciones) (2 bytes)

        # Campos para sincronización del nodo
        "Timestamp": datetime.now(),  # Marca de tiempo actual del Sink o CH
        "IsSynced": False,  # Indica si el nodo está sincronizado

        # Campos para el proceso del Tangle IOTA - Autenticación
        "Tips": [],  # Almacena los tips de transacciones no aprobadas
        "ApprovedTransactions": [],  # Transacciones aprobadas por este nodo
        "Transactions": [],  # Transacciones generadas por este nodo

        # Proceso de autenticación
        "Authenticated": False,  # Estado de autenticación del nodo
        "ExclusionStatus": False,  # Estado de exclusión si no se autentica a tiempo
        "TimeoutStart": datetime.now().timestamp(),  # Registro del tiempo en que se inicia la autenticación

        # "SharedKey": np.zeros(32, dtype=np.uint8),  # Clave compartida (256 bits = 32 bytes)

        # Lista de claves públicas de los nodos registrados en la red antes del despliegue
        "RegisterNodes": [],  # Lista de diccionarios con NodeID, Status (IsSyn or Is Auth)

        # Clave publica del sink
        "PublicKey_sign_sink" : public_key_sign_sink, # Clave pública para firmas (256 bits = 32 bytes)
        "PublicKey_shared_sink" : public_key_shared_sink # Clave pública para secreto compartido (256 bits = 32 bytes)
    }
    return node


def create_key_sink():
    # Generación de par de claves para firmar y verificar mensajes utilizando ed25519
    ed25519_private_key = ed25519.Ed25519PrivateKey.generate()
    ed25519_public_key = ed25519_private_key.public_key()

    # Convertir la clave privada Ed25519 a bytes (formato raw)
    ed25519_private_key_bytes = ed25519_private_key.private_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PrivateFormat.Raw,
        encryption_algorithm=serialization.NoEncryption()
    )

    # Convertir la clave publica Ed25519 a bytes (formato raw)
    ed25519_public_key_bytes = ed25519_public_key.public_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PublicFormat.Raw,
    )

    # Generación de par de claves para establecer clave compartida utilizando x25519
    x25519_private_key = x25519.X25519PrivateKey.generate()
    x25519_public_key = x25519_private_key.public_key()

        # Convertir la clave privada Ed25519 a bytes (formato raw)
    x25519_private_key_bytes = x25519_private_key.private_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PrivateFormat.Raw,
        encryption_algorithm=serialization.NoEncryption()
    )

    # Convertir la clave publica Ed25519 a bytes (formato raw)
    x25519_public_key_bytes = x25519_public_key.public_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PublicFormat.Raw,
    )
   
    return ed25519_private_key_bytes, ed25519_public_key_bytes, x25519_private_key_bytes, x25519_public_key_bytes


# def load_key_node_bbdSqlite()

def create_num_nodes(num_nodes, pos_nodes, E_init, public_key_sign_sink, public_key_shared_sink):
    node_uw = []  # Lista para almacenar la estructura de cada nodo
    for node in range(num_nodes):
        # Ejemplo de cómo buscar una clave específica para firmas en la bbdd
        key_private_sign, key_public_sign = load_keys_sign_withou_cipher("bbdd_keys_shared_sign_cipher.db", "keys_sign_ed25519", index=node+1)

        # Ejemplo de cómo buscar una clave específica para secreto compartido en la bbdd
        key_private_shared, key_public_shared = load_keys_shared_withou_cipher("bbdd_keys_shared_sign_cipher.db", "keys_shared_x25519", index=node+1)

        print('Keys sign : Indice : ', node + 1, ' Private key sign : ', key_private_sign.hex(), ' Public key sign : ', key_public_sign.hex())
        print('Keys shared : Indice : ', node + 1, ' Private key shared : ', key_private_shared.hex(), ' Public key shared: ', key_public_shared.hex())

        # Obtener la posición del nodo
        pos_x, pos_y, pos_z = pos_nodes[node]

        # Almacenar información del nodo en su estructura
        node_uw.append(create_node(node+1, [pos_x, pos_y, pos_z], E_init, node+1, key_private_sign, key_public_sign, 
                                   node+1, key_private_shared, key_public_shared, public_key_sign_sink, public_key_shared_sink))

    return node_uw


## Función para asignar el par de claves de forma randomica
import random

def create_num_nodes_random(num_nodes, pos_nodes, E_init, public_key_sign_sink, public_key_shared_sink):
    node_uw = []  # Lista para almacenar la estructura de cada nodo
    
    # Crear una lista de índices de las claves disponibles (del 1 al 1000)
    sign_key_indices = list(range(1, 1001))
    shared_key_indices = list(range(1, 1001))
    
    # Barajar los índices para que la selección sea aleatoria
    random.shuffle(sign_key_indices)
    random.shuffle(shared_key_indices)
    
    # Limitar la selección a los primeros 'num_nodes' para asegurar que se usen índices únicos
    selected_sign_keys = sign_key_indices[:num_nodes]
    selected_shared_keys = shared_key_indices[:num_nodes]
    
    for node in range(num_nodes):
        # Seleccionar índices únicos para cada nodo
        index_sign = selected_sign_keys[node]
        index_shared = selected_shared_keys[node]
        
        # Buscar clave específica para firmas en la bbdd usando el índice seleccionado
        key_private_sign, key_public_sign = load_keys_sign_withou_cipher("bbdd_keys_shared_sign_cipher.db", "keys_sign_ed25519", index=index_sign)

        # Buscar clave específica para secreto compartido en la bbdd usando el índice seleccionado
        key_private_shared, key_public_shared = load_keys_shared_withou_cipher("bbdd_keys_shared_sign_cipher.db", "keys_shared_x25519", index=index_shared)

        print('Keys sign : Indice : ',  index_sign, ' Private key sign : ', key_private_sign.hex(), ' Public key sign : ', key_public_sign.hex())
        print('Keys shared : Indice : ', index_shared, ' Private key shared : ', key_private_shared.hex(), ' Public key shared: ', key_public_shared.hex())

        # Obtener la posición del nodo
        pos_x, pos_y, pos_z = pos_nodes[node]

        # Almacenar información del nodo en su estructura
        node_uw.append(create_node(node+1, [pos_x, pos_y, pos_z], E_init, index_sign, key_private_sign, key_public_sign, 
                                   index_shared, key_private_shared, key_public_shared, public_key_sign_sink, public_key_shared_sink))

    return node_uw
