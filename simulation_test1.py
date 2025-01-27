
# %% PARAMETROS INICIALES DE SIMULACIÓN
import numpy as np
from bbdd_sqlite3 import generar_claves_sin_cifrado

print ('PARAMETROS DE SIMULACIÓN...')
# PARAMETROS DE LA RED INICIAL
# Parámetros de la red de nodos
num_nodes = 20  # Número de nodos
dim_x = 100  # Dimensiones del área de despliegue (en metros)
dim_y = 100
dim_z = -100  # Profundidad (en metros)
sink_pos = np.array([50, 50, 0])  # Posición del Sink en el centro
E_init = 10  # Energía inicial de cada nodo (en Joules)

# Frecuencia de transmisión en kHz
freq = 20  # Ajusta la frecuencia según el entorno de la red subacuática

# Configuración del modelo de energía basado en el artículo de Yang
L = 2000  # Tamaño del paquete de datos (bits)
a = 80  # Tamaño del paquete de control (bits)
EDA = 5 * 10**-9  # Energía para la agregación de datos (Joules/bit)
E_schedule = 5 * 10**-9  # Energía de programación (Joules/bit)
P_r = 1 * 10**-3  # Potencia de recepción (Joules/bit)
threshold_bateria = 1  # Umbral de energía de la batería (Joules)

# Posicionamiento de los nodos (valores aleatorios dentro del área de despliegue)
pos_nodes = np.random.rand(num_nodes, 3) * [dim_x, dim_y, dim_z]

# Como el eje z representa profundidad negativa, ajustamos la coordenada z
pos_nodes[:, 2] = pos_nodes[:, 2] * (-1)

# crea la Base de datos para los nodos
generar_claves_sin_cifrado("claves_sin_cifrado.db")

##############

# %% CREACIÓN DEL NODO SINK
from create_nodes import create_key_sink, create_sink

print ('CREANDO SINK CON SU PAR DE CLAVES...')
private_bytes_sink, public_bytes_sink = create_key_sink()

print('clave publica : ', public_bytes_sink)
print('Clave privada : ', private_bytes_sink)

# Crear el nodo Sink
node_sink = create_sink(0, sink_pos, private_bytes_sink, public_bytes_sink)


# %% CREACIÓN DE LOS NODOS A DESPLEGAR
from create_nodes import create_num_nodes

print('CREANDO NODOS, ASIGNANDO PAR DE CLAVES DE BBDD SQLITE...')

public_key_sink = node_sink['PublicKey']

node_uw = create_num_nodes(num_nodes, pos_nodes, public_key_sink, E_init, node_sink)

print("FINAL DE CREACIóN DEL SINK Y NODOS...")
######



######


# %% PROCESO DE ESTABLECIMIENTO DE CLUSTER

from cluster import classify_levels, select_cluster_heads, assign_to_clusters, update_energy, acoustic_loss

print ('PROCESO DE CREACIÓN DE CLUSTER...')

## Proceso de generación de cluster

num_rounds = 1
num_niveles = 3
radio_comunicacion = 50

# Inicialización de energía

energia_nodos = np.full(num_nodes, E_init)

# Precalcular la matriz de distancias entre todos los nodos

distancias = np.linalg.norm(pos_nodes[:, np.newaxis] - pos_nodes, axis=2)

for round in range(num_rounds):
    # Calcular distancias al sink y niveles de los nodos

    dist_al_sink = np.linalg.norm(pos_nodes - sink_pos, axis=1)

    niveles = classify_levels(dist_al_sink, num_niveles)  # Clasificación en niveles


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

print('NeighboarSink : ',node_sink['NeighborCHs'])


for i in range(num_nodes):

    print('indice : ' , i , node_uw[i]['NodeID'], ' - ', node_uw[i]['ClusterHead'], ' - ', node_uw[i]['NumCluster'], ' : ', node_uw[i]['NeighborNodes'])

################


# %%    PROCESO DE SINCRONIZACIÓN

from syn import propagate_syn_to_CH, propagate_syn_to_CH_cdma, clear_sync_state
from save_csv import save_stats_to_csv, save_stats_to_csv_cdma

# Borrar la sincronización establecida

clear_sync_state(node_uw)

### SINCRONIZACIÓN DE NODO

max_retries = 3
timeout = 2
freq=20

print ('INICIO PROCESO DE SINCRONIZACIÓN DE NODOS DENTRO DEL CLUSTER CDMA...')

# Sincronización basada en CDMA

syn_packet, stats_cdma = propagate_syn_to_CH_cdma(node_sink, CH, node_uw, max_retries, timeout, freq)

print(" - ")

print('Resultados CDMA')
for i in range(num_nodes):
    print('indice : ' , i , node_uw[i]['NodeID'], '     - ', node_uw[i]['ClusterHead'], '   - ', node_uw[i]['NumCluster'],
          ' : ', node_uw[i]['IsSynced'], ' : ', node_uw[i]['ResidualEnergy']
          , ' : ', node_uw[i]['Role'])

print("Estadísticas CDMA:")
print(f"Nodos sincronizados exitosamente: {stats_cdma['sync_success']}")
print(f"Nodos fallidos en sincronización: {stats_cdma['sync_failures']}")
print(f"Retransmisiones totales: {stats_cdma['total_retransmissions']}")
print(f"Energía total consumida: {stats_cdma['total_energy_consumed']}")
print(f"Energía total consumida por escuchas: {stats_cdma['total_energy_listen']}")
print(f"Tiempos de sincronización: {stats_cdma['sync_times']}")

save_stats_to_csv_cdma('sync_stats_cdma.csv', stats_cdma, 'CDMA')


######################

# %%    AUTENTICACIÓN CON TANGLE
from propagacionTx import propagate_tx_to_ch
from tangle import create_gen_block, delete_tangle
import time
from save_csv import save_stats_tx

# Llamada a la función

delete_tangle(node_sink, node_uw, CH)


# Captura de estadisticas
# Inicializar estadísticas
stats_tx = {
    "times_createTxgen": [],
    "times_verifyTx": [],
    "times_Txresponse": [],
}

# Crear la Tx genesis

print ('AUTENTICACIÓN CON TANGLE...')

rondas = 100

for i in range(rondas):
    print('Ronda de calculo de creación y verificación de Tx : ', i+1)
    ####
    # Crear la genesis

    timestart = time.time() # inicio de la creación de tx genesis
    txgenesis = create_gen_block(node_sink["NodeID"], node_sink["PrivateKey"])
    time_createTX = time.time() - timestart
    print('Tiempo de creación de Tx genesis Sink: ', time_createTX)
    print('Bloque genesis', txgenesis)


    print ('PROPAGACIÓN DE LA TX GENESIS A LOS CH...')

    recived, end_time_verify, end_time_responseCH = propagate_tx_to_ch(node_sink, CH, node_uw, txgenesis)

    # Convertir las listas a cadenas para almacenarlas
    time_verify_str = ','.join(map(str, end_time_verify))
    time_response_str = ','.join(map(str, end_time_responseCH))

    print('Tiempo de verificación de Tx genesis por CH or SN : ', end_time_verify)
    print('Tiempo de creación de Tx response por CH or SN: ', end_time_responseCH)

    stats_tx["times_createTxgen"].append(time_createTX)
    stats_tx["times_verifyTx"].append(end_time_verify)
    stats_tx["times_Txresponse"].append(end_time_responseCH)

save_stats_tx('stats_tx.csv', stats_tx)
print('Las estadisticas se alamacenaron...')

####
