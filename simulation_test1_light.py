# %% PARAMETROS INICIALES DE SIMULACIÓN
import numpy as np
from bbdd2_sqlite3 import generarte_keys_shared_without_cipher, generarte_keys_sign_without_cipher

print ('PARAMETROS DE SIMULACIÓN...')
# PARAMETROS DE LA RED INICIAL
# Parámetros de la red de nodos
num_nodes = 20  # Número de nodos
dim_x = 200  # Dimensiones del área de despliegue (en metros)
dim_y = 200
dim_z = -200  # Profundidad (en metros)
sink_pos = np.array([100, 100, 0])  # Posición del Sink en el centro
E_init = 10  # Energía inicial de cada nodo (en Joules)

# Frecuencia de transmisión en kHz
freq = 20  # Ajusta la frecuencia según el entorno de la red subacuática

# Configuración del modelo de energía basado en el artículo de Yang
L = 2000  # Tamaño del paquete de datos (bits)
size_packet_control = 80  # Tamaño del paquete de control (bits)
EDA = 5 * 10**-9  # Energía para la agregación de datos (Joules/bit)
E_schedule = 5 * 10**-9  # Energía de programación (Joules/bit)
P_r = 1 * 10**-3  # Potencia de recepción (Joules/bit)
threshold_bateria = 1  # Umbral de energía de la batería (Joules)

# Posicionamiento de los nodos (valores aleatorios dentro del área de despliegue)
pos_nodes = np.random.rand(num_nodes, 3) * [dim_x, dim_y, dim_z]

# Como el eje z representa profundidad negativa, ajustamos la coordenada z
pos_nodes[:, 2] = pos_nodes[:, 2] * (-1)

# crea la Base de datos para los nodos
generarte_keys_shared_without_cipher("bbdd_keys_shared_sign_cipher.db")
generarte_keys_sign_without_cipher("bbdd_keys_shared_sign_cipher.db")

print('-')
##############

# %% CREACIÓN DEL NODO SINK
from create_nodes_light import create_key_sink, create_sink
print('-')
print ('CREANDO SINK CON SU PAR DE CLAVES ES EL ÚNICO QUE VA A GENERAR CLAVES PROPIAS...')
ed25519_private_key, ed25519_public_key, x25519_private_key, x25519_public_key = create_key_sink()

print('clave publica : ', ed25519_private_key)
print('Clave privada : ', ed25519_public_key)
print('clave publica : ', x25519_private_key)
print('Clave privada : ', x25519_public_key)

# Crear el nodo Sink
node_sink = create_sink(0, sink_pos, ed25519_private_key, ed25519_public_key, x25519_private_key, x25519_public_key)

print("FINAL DE CREACIóN DEL SINK...")
print('-')
################

# %% CREACIÓN DE LOS NODOS A DESPLEGAR
from create_nodes_light import create_num_nodes, create_num_nodes_random
print('-')
print('CREANDO NODOS, UTILIZARAN LA BBDD DE CLAVES PUBLICAS Y PRIVADAS')

public_key_sign_sink = node_sink['PublicKey_sign']
public_key_shared_sink = node_sink['PublicKey_shared']

# node_uw = create_num_nodes(num_nodes, pos_nodes, E_init, public_key_sign_sink, public_key_shared_sink)
node_uw = create_num_nodes_random(num_nodes, pos_nodes, E_init, public_key_sign_sink, public_key_shared_sink)

print("FINAL DE CREACIóN NODOS A DESPLEGAR, CADA UNO ALAMACENA LAS CLAVES PUBLICAS DEL SINK...")
print('-')
######

#%%
print('-')
print("INICIALIZACIÓN DE NODOS EN EL SINK STATUS(SYN=FALSE; AUTH=FALSE)...")

# Guardar el estado de cada nodo en el sink
for node in range(num_nodes):
    node_sink["RegisterNodes"].append({
        "NodeID": node_uw[node]["NodeID"],
        "Status_syn": False,
        "Status_auth": False
    })

print("FIN DE INICIALIZACIÓN DE NODOS...")
print('-')
######


# %% PROCESO DE ESTABLECIMIENTO DE CLUSTER

from cluster import classify_levels, select_cluster_heads, assign_to_clusters, update_energy, acoustic_loss
print('-')
print ('INICIO DE PROCESO DE CREACIÓN DE CLUSTER...')

## Proceso de generación de cluster
num_rounds = 1
num_niveles = 3
radio_comunicacion = 100

# Inicialización de energía
energia_nodos = np.full(num_nodes, E_init)

# Precalcular la matriz de distancias entre todos los nodos
distancias = np.linalg.norm(pos_nodes[:, np.newaxis] - pos_nodes, axis=2)

for round in range(num_rounds):
    # Calcular distancias al sink y niveles de los nodos
    dist_al_sink = np.linalg.norm(pos_nodes - sink_pos, axis=1)

    # Clasificación en niveles
    niveles = classify_levels(dist_al_sink, num_niveles)  

    # Selección de Cluster Heads
    CH = select_cluster_heads(energia_nodos, niveles, threshold_bateria)

    # Verificar si se seleccionaron CHs suficientes
    if len(CH) == 0:
        print(f"No se seleccionaron Cluster Heads en la ronda {round + 1}.")
        continue  # Saltar a la siguiente ronda

    # Asociación de nodos a Cluster Heads
    idx_CH = assign_to_clusters(pos_nodes, pos_nodes[CH, :])

    # Verificar si la asignación fue exitosa
    if len(idx_CH) == 0:
        print(f"La asignación de nodos a Cluster Heads falló en la ronda {round + 1}.")
        continue  # Saltar a la siguiente ronda

    for c, CH_id in enumerate(CH):
        print(c, ' - ', CH_id)

        # Asignar rol de Cluster Head
        node_uw[CH_id]["Role"] = 1  # 1 = Cluster Head
        node_uw[CH_id]["ClusterHead"] = CH_id + 1
        node_uw[CH_id]["NumCluster"] = c + 1
        node_uw[CH_id]["NeighborNodes"] = []  # Inicializar la lista de NeighborNodes como vacía

        # Encuentra los vecinos (nodos normales) asignados a este CH
        vecinos = np.where(idx_CH == c)[0]

        # Excluir el propio CH (CH_id + 1) de la lista de vecinos
        vecinos = vecinos[vecinos != (CH_id)]  # Filtrar el propio CH

        node_uw[CH_id]["NeighborNodes"] = (vecinos + 1).tolist()

        # Asignar los CH como vecinos del Sink
        node_sink["NeighborCHs"] = np.append(node_sink["NeighborCHs"], np.uint16(CH_id + 1))

        # # 2. Actualizar la información de los nodos normales
        for nodo_id in range(num_nodes):
        #     print('pregunta : ', nodo_id, '  ', CH)
            if nodo_id not in CH:
                # Verificar si el nodo está asignado al CH actual
                if idx_CH[nodo_id] == c:
                    # Encontrar vecinos cercanos para este nodo
                    vecinos_cercanos = np.where((distancias[nodo_id] <= radio_comunicacion) & (distancias[nodo_id] > 0))[0]

                    # Actualizar la información del nodo
                    node_uw[nodo_id]["Role"] = 2  # Rol: 2 = Nodo Sensor
                    node_uw[nodo_id]["NumCluster"] = c + 1
                    node_uw[nodo_id]["ClusterHead"] = CH_id + 1
                    # node_uw[nodo_id]["NeighborNodes"] = (vecinos_cercanos + 1).tolist()

                    # Almacenar los vecinos en el rango de comunicación, y agregar el Cluster Head como vecino
                    vecinos_cercanos_ids = (vecinos_cercanos + 1).tolist()  # Convertir a NodeIDs

                    # print('id ', CH_id,'ccc : ', vecinos_cercanos_ids)
                    if CH_id + 1 not in vecinos_cercanos_ids:  # Asegurarse de que no esté duplicado
                        vecinos_cercanos_ids.append(CH_id + 1)  # Agregar el CH al final de los vecinos

                    node_uw[nodo_id]["NeighborNodes"] = vecinos_cercanos_ids

# print(node_uw[1]['NodeID'])
print('NeighboarSink : ', node_sink['NeighborCHs'])

for i in range(num_nodes):
    print('indice : ' , i , node_uw[i]['NodeID'], ' - ', node_uw[i]['ClusterHead'], ' - ', node_uw[i]['NumCluster'], ' : ', node_uw[i]['NeighborNodes'])

print('FIN DE PROCESO DE CREACIÓN DE CLUSTER...')
print('-')
################

# #%%
# # ###################

# print ('INICIO PROCESO DE GUARDADO NODOS EN ARCHIVO PICKLE...')
# # ## GUARDAR LA ESTRUCTURA HASTA ESTE MOMENTO
# # import json
# import pickle
# import os

# # Obtener la ruta del directorio donde se encuentra el script actual
# # current_dir = os.path.dirname(os.path.abspath(__file__))
# current_dir = os.getcwd()

# # Definir la carpeta donde se encuentra la base de datos (carpeta 'save_struct')
# carpeta_destino = os.path.join(current_dir, 'save_struct')

# # Crea la carpeta en caso de no existir
# if not os.path.exists(carpeta_destino):
#     os.makedirs(carpeta_destino)

# # Ruta completa del archivo de la base de datos dentro de la carpeta 'save_struct'
# ruta_nodos = os.path.join(carpeta_destino, 'nodos_guardados.pkl')
# ruta_sink = os.path.join(carpeta_destino, 'sink_guardado.pkl')

# # Supongamos que node_uw es tu lista de nodos
# with open(ruta_nodos, 'wb') as file:
#     pickle.dump(node_uw, file)

# # Guardamos el sink en un archivo para luego utilizarla
# with open(ruta_sink, 'wb') as file:
#     pickle.dump(node_sink, file)

# print ('FIN PROCESO DE GUARDADO NODOS EN ARCHIVO PICKLE...')

# #################


# %%    PROCESO DE SINCRONIZACIÓN

print('-')
print ('INICIO DE PROCESO DE SYNCRONIZACIÓN...')

from syn_light import propagate_syn_to_CH_tdma, propagate_syn_to_CH_cdma, clear_sync_state
from save_csv import save_stats_to_csv, save_stats_to_csv_cdma, save_stats_to_syn_csv

# # Borrar la sincronización establecida
# clear_sync_state(node_sink, node_uw, CH)

### SINCRONIZACIÓN DE NODO
max_retries = 3
timeout = 2
freq=20
processing_energy_cdma=5e-9
alpha=1e-6
E_listen=1e-9
E_standby=1e-12

# Por ahora solo se va a utilizar TDMA
# print('-')
# print ('INICIO DE PROCESO DE SYNCRONIZACIÓN SIMULANDO CDMA...')

# # Sincronización basada en CDMA
# # syn_packet, stats_cdma = propagate_syn_to_CH_cdma(node_sink, CH, node_uw, max_retries, timeout, freq)
# syn_packet, stats_cdma = propagate_syn_to_CH_cdma(node_sink, CH, node_uw, max_retries, timeout, freq, processing_energy_cdma, size_packet_control, alpha, P_r, E_listen, E_standby)

# print(" - ")
# print('Resultados CDMA')

# # save_stats_to_csv_cdma('sync_stats_cdma.csv', stats_cdma, 'CDMA')
# save_stats_to_syn_csv('sync_stats_cdma.csv', stats_cdma, 'CDMA')

# print ('FIN DE PROCESO DE SYNCRONIZACIÓN SIMULANDO CDMA...')
# print('-')

# # Borrar la sincronización establecida
# clear_sync_state(node_sink, node_uw, CH)

print("-")
print("INCIO PROCESO DE SINCRONIZACIÓN CON TDMA")

# Sincronización basada en CDMA
# syn_packet, stats_cdma = propagate_syn_to_CH_cdma(node_sink, CH, node_uw, max_retries, timeout, freq)
syn_packet, stats_tdma = propagate_syn_to_CH_tdma(node_sink, CH, node_uw, max_retries, timeout, freq, E_schedule, size_packet_control, alpha, P_r, E_standby)

print(" - ")
print('Resultados TDMA')

# save_stats_to_csv_cdma('sync_stats_tdma.csv', stats_tdma, 'TDMA')
save_stats_to_syn_csv('sync_stats_tdma.csv', stats_tdma, 'TDMA')

print("FIN PROCESO DE SINCRONIZACIÓN CON TDMA")
print("-")

######################

# %%    AUTENTICACIÓN CON TANGLE

print("-")
print("INCIO PROCESO DE AUTENTICACIÓN BASADO EN TX")

from propagacionTx_light import propagate_tx_to_ch, authenticate_nodes_to_ch, propagate_tx_to_sink_and_cluster
from tangle2_light import create_gen_block, delete_tangle
import time
from save_csv import save_stats_tx

# Llamada a la función

delete_tangle(node_sink, node_uw, CH)


# Captura de estadisticas
# Inicializar estadísticas
stats_tx = {
    "times_createTxgen": [],
    "times_verifyTx_toCH": [],
    "times_TxresponseCH": [],
    "times_propagation_txgen": [],
    "times_propagation_response_tx": [],
}

# Crear la Tx genesis
print("-")
print ('AUTENTICACIÓN CON TANGLE...')

rondas = 1

for i in range(rondas):
    print('Ronda de calculo de creación y verificación de Tx : ', i+1)
    ####
    # Crear la genesis

    print('Clave del sink : ', node_sink["PrivateKey_sign"])

    node_sink["PrivateKey_sign"]

    timestart = time.time() # inicio de la creación de tx genesis
    txgenesis = create_gen_block(node_sink["NodeID"], node_sink["PrivateKey_sign"])
    time_createTX = time.time() - timestart

    node_sink["Tips"].append(txgenesis["ID"])   # Agrega la Tx genesis a la lista de tips
    node_sink['Transactions'].append(txgenesis) # Agrega la Tx genesis a la lsita de Transactions

    print('Tiempo de creación de Tx genesis Sink: ', time_createTX)
    print('Bloque genesis', txgenesis)

    print("-")
    print ('PROPAGACIÓN DE LA TX GENESIS A LOS CH...')

    # propagación de la tx genesis hacia los ch y nodos de cada cluster
    # en caso de recibir y verificar la tx genesis y verificarla la propaga hacia los nodos de su cluster
    # el ch prepara la tx de autenticación que la remite de vuelta al sink,el ch no se autentica mientras el sink
    #  no valide la tx de respuesta
    # Este proceso solo se lleva a cabo siempre y cuando los ch esten sincronizados.
    recived, end_time_verify, times_propagation_tx = propagate_tx_to_ch(node_sink, CH, node_uw, txgenesis)

    # Crear la tx de respuesta de los CH y transmitirlas al sink y los nodos del cluster
    end_time_responseCH, end_time_propagationTxCh = propagate_tx_to_sink_and_cluster(node_sink, CH, node_uw)

    print("-")
    print('AUTENTICACIÓN DE LOS NODOS DEL CLUSTER')
    # Creación y propagación de la tx de autenticación de los nodos de cada cluster
    authenticate_nodes_to_ch(node_uw, CH)

    # Convertir las listas a cadenas para almacenarlas
    time_verify_str = ','.join(map(str, end_time_verify))
    time_response_str = ','.join(map(str, end_time_responseCH))

    print('Tiempo de verificación de Tx genesis por CH or SN : ', end_time_verify)
    print('Tiempo de creación de Tx response por CH or SN: ', end_time_responseCH)

    stats_tx["times_createTxgen"].append(time_createTX)
    stats_tx["times_propagation_txgen"].append(times_propagation_tx)
    stats_tx["times_verifyTx_toCH"].append(end_time_verify)
    stats_tx["times_TxresponseCH"].append(end_time_responseCH)
    stats_tx["times_propagation_response_tx"].append(end_time_propagationTxCh)

save_stats_tx('stats_tx.csv', stats_tx)
print('Las estadisticas se almacenaron...')

print("FIN PROCESO DE AUTENTICACIÓN BASADO EN TX")

# ####

print('Nodo Sink : ', node_sink)


#%%
## INICIO PROCESO DE TRANSMISIÓN DE DATOS CIFRADOS CON ASCON
print("-")
print ('INICIO PROCESO DE TRANSMISIÓN DE DATOS CIFRADOS CON ASCON...')
from transmit_data_test import create_shared_keys_table, generate_shared_keys, transmit_data

# Se crea la tabla en la BBDD donde se van a crear las claves compartidas
create_shared_keys_table("bbdd_keys_shared_sign_cipher.db")

# 📌 Generar claves compartidas después de la autenticación
generate_shared_keys("bbdd_keys_shared_sign_cipher.db", node_uw, CH, node_sink)

# Número total de transmisiones que queremos completar
total_transmissions = 30
completed_transmissions = 0  # Contador de transmisiones realizadas
max_attempts = 100  # Para evitar un bucle infinito si no hay nodos elegibles
attempts = 0

attempts = 0
while completed_transmissions < total_transmissions and attempts < max_attempts:
    attempts += 1  # Contador de intentos para evitar bucles infinitos
    
    # Seleccionamos un nodo aleatorio
    sender_index = np.random.randint(0, len(node_uw))  # Selección aleatoria de nodo
    sender = node_uw[sender_index]

    # Obtener el ID del Cluster Head (CH)
    # ch_id = sender.get("ClusterHead")
    ch_id = sender["ClusterHead"]
    # print("Sender : ", ch_id)

    # Validar que el nodo tiene un Cluster Head asignado
    if ch_id is None or ch_id == sender["NodeID"]:
        print("Detiene en caso de no tener CH asignado o es el mismo nodo...")
        continue  # Saltar si el nodo no tiene CH o si es su propio CH

    # Obtener el nodo Cluster Head
    receiver = node_uw[ch_id - 1]
    # print("Receiver : ", receiver["NodeID"])
    # time.sleep(1)

    # verificar que datos se envian
    # print(" Sender : ",sender["NodeID"],"-> Receiver : ", receiver["NodeID"])

    # Transmitir datos
    transmit_data("bbdd_keys_shared_sign_cipher.db", sender, receiver, f"Temperatura: {np.random.uniform(5, 30):.2f}°C")

    completed_transmissions += 1  # Incrementar transmisiones realizadas

# 📌 Simulación de CH enviando datos al Sink
for ch in CH:
    node_cluster = node_uw[ch]
    transmit_data("bbdd_keys_shared_sign_cipher.db", node_cluster, node_sink, "Datos agregados del cluster")

print(f"✅ Simulación completa: {completed_transmissions}/{total_transmissions} transmisiones realizadas.")


print("-")
print ('FIN PROCESO DE TRANSMISIÓN DE DATOS CIFRADOS CON ASCON...')
#%%

# %%
#%%

# ###################
print("-")
print ('INICIO PROCESO DE GUARDADO NODOS EN ARCHIVO PICKLE...')
# ## GUARDAR LA ESTRUCTURA HASTA ESTE MOMENTO
# import json
import pickle
import os

# Obtener la ruta del directorio donde se encuentra el script actual
# current_dir = os.path.dirname(os.path.abspath(__file__))
current_dir = os.getcwd()

# Definir la carpeta donde se encuentra la base de datos (carpeta 'save_struct')
carpeta_destino = os.path.join(current_dir, 'save_struct')

# Crea la carpeta en caso de no existir
if not os.path.exists(carpeta_destino):
    os.makedirs(carpeta_destino)

# Ruta completa del archivo de la base de datos dentro de la carpeta 'save_struct'
ruta_nodos = os.path.join(carpeta_destino, 'nodos_guardados.pkl')
ruta_sink = os.path.join(carpeta_destino, 'sink_guardado.pkl')

# Supongamos que node_uw es tu lista de nodos
with open(ruta_nodos, 'wb') as file:
    pickle.dump(node_uw, file)

# Guardamos el sink en un archivo para luego utilizarla
with open(ruta_sink, 'wb') as file:
    pickle.dump(node_sink, file)

print ('FIN PROCESO DE GUARDADO NODOS EN ARCHIVO PICKLE...')

#################