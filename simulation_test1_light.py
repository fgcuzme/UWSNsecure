# main_sim.py
def run_one(RUN_NUM:int, SEED:int, NUM_NODES:int,
            output_dir: str = None):
    import os, json, datetime, random, numpy as np
    random.seed(SEED); np.random.seed(SEED)

    SCENARIO_ID = os.environ.get("SCENARIO_ID", "1000km_W5_Sh0.5")
    RUN_ID = f"{SCENARIO_ID}_seed{SEED}_run{RUN_NUM:02d}"
    SHIPPING = os.environ.get("SHIPPING", None)
    WIND_SPEED = os.environ.get("WIND_SPEED", None)
    ENERGY_INI = os.environ.get("UWSN_ENERGY_INITIAL_J", "100.0")

    output_dir = output_dir or f"stats/{RUN_ID}/"
    # os.makedirs("stats", exist_ok=True)
    os.makedirs(output_dir, exist_ok=True)

    with open(os.path.join(output_dir, f"manifest_{RUN_ID}.json"), "w") as f:
    # with open(f"stats/manifest_{RUN_ID}.json","w") as f:
        json.dump({
            "run_id": RUN_ID,
            "seed": SEED,
            "scenario": {
                "num_nodes": NUM_NODES,
                "freq_khz": 20, "bitrate_bps": 9200,
                "traffic_shipping = 0.5": float(SHIPPING), "wind_mps": float(WIND_SPEED),
                "spreading": 1.5,
                "E_init_J": float(ENERGY_INI), "threshold_bateria": float(0.10*float(ENERGY_INI))
            },
            "start_time": datetime.datetime.utcnow().isoformat(),
            "code_version": "v1.0-main"
        }, f, indent=2)


    # %% PARAMETROS INICIALES DE SIMULACIÓN
    import numpy as np
    from bbdd2_sqlite3 import generarte_keys_shared_without_cipher, generarte_keys_sign_without_cipher
    # from clock_uan import sim_advance, sim_now_ms
    import csv, math

    num_nodes = NUM_NODES  # Número de nodos

    # ## 28/09/2025
    # # === Reproducibilidad y metadatos del experimento ===
    # import os, json, datetime, random

    # SEED = int(os.environ.get("UWSN_SEED", "1337"))
    # random.seed(SEED); np.random.seed(SEED)

    # SCENARIO_ID = os.environ.get("SCENARIO_ID", "1000km_W5_Sh0.5")  # si quieres, ajusta luego
    # RUN_NUM = int(os.environ.get("RUN", "1"))
    # RUN_ID = f"{SCENARIO_ID}_seed{SEED}_run{RUN_NUM:02d}"

    # os.makedirs("stats", exist_ok=True)
    # manifest = {
    #     "run_id": RUN_ID,
    #     "seed": SEED,
    #     "scenario": {
    #         "num_nodes": num_nodes,
    #         "freq_khz": 20, "bitrate_bps": 9200,
    #         "traffic_shipping": 0.5, "wind_mps": 5,
    #         "spreading": 1.5,
    #         "E_init_J": 100, "threshold_bateria": float(0.10*100)
    #     },
    #     "start_time": datetime.datetime.utcnow().isoformat(),
    #     "code_version": "v1.0-main"
    # }
    # with open(f"stats/manifest_{RUN_ID}.json","w") as f:
    #     json.dump(manifest, f, indent=2)


    ###########################
    ###########################

    print ('PARAMETROS DE SIMULACIÓN...')
    # PARAMETROS DE LA RED INICIAL
    # Parámetros de la red de nodos
    # num_nodes = 20  # Número de nodos
    # dim_x = 1000  # Dimensiones del área de despliegue (en metros)
    # dim_y = 1000
    # dim_z = -1000  # Profundidad (en metros)
    # sink_pos = np.array([500, 500, 0])  # Posición del Sink en el centro
    # E_init = 10  # Energía inicial de cada nodo (en Joules)

    # pasadas por parametros
    dim_x = int(os.environ.get("DIM_X", "1000"))
    dim_y = int(os.environ.get("DIM_Y", "1000"))
    dim_z = int(os.environ.get("DIM_Z", "-1000"))
    sink_pos = np.array([
    float(os.environ.get("SINK_POS_X", "500")),
    float(os.environ.get("SINK_POS_Y", "500")),
    float(os.environ.get("SINK_POS_Z", "0"))
    ])

    # Estimación de la capacidad de batería necesaria para tus nodos acústicos subacuáticos,
    # basado en las especificaciones del módem S2CR 15/27 (15–27 kHz) y tu perfil de tráfico.
    # Este diseño es ideal para despliegues controlados (12–24 h), como misiones de muestreo
    #  temporal o experimentación oceanográfica.
    # Ref: chrome-extension://efaidnbmnnnibpcajpcglclefindmkaj/https://www.evologics.com/web/content/15634?unique=be7aa65d1c113e56664940ddea7cf65757e6648e
    E0 = float(ENERGY_INI)
    E_init = E0  # Energía inicial realista en julios (≈ 0.9 Ah @ 3.7V)

    # Frecuencia de transmisión en kHz
    freq = 20  # Ajusta la frecuencia según el entorno de la red subacuática

    # Configuración del modelo de energía basado en el artículo de Yang
    # L = 2000  # Tamaño del paquete de datos (bits)
    size_packet_control = 72  # Tamaño del paquete de control (bits)
    EDA = 5 * 10**-9  # Energía para la agregación de datos (Joules/bit)
    E_schedule = 5 * 10**-9  # Energía de programación (Joules/bit) # Joules/bit = 5 nJ/bit
    # P_r = 1 * 10**-3  # Potencia de recepción (Joules/bit)
    # threshold_bateria = 1  # Umbral de energía de la batería (Joules)

    # Se ajusta el umbral de la capacidad de la bateria en vista que la carga inicial de los nodos aumenta
    # threshold_bateria = 0.357 * E_init  # 10% de la capacidad
    threshold_bateria = 0.10 * E_init  # 10% de la capacidad

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

    from cluster import classify_levels, select_cluster_heads, assign_to_clusters
    print('-')
    print ('INICIO DE PROCESO DE CREACIÓN DE CLUSTER...')

    ## Proceso de generación de cluster
    num_rounds = 1
    num_niveles = 3
    # radio_comunicacion = 500

    radio_comunicacion = float(os.environ.get("RADIO_RANGE", "500"))

    # Inicialización de energía
    energia_nodos = np.full(num_nodes, E_init)

    # Precalcular la matriz de distancias entre todos los nodos
    distancias = np.linalg.norm(pos_nodes[:, np.newaxis] - pos_nodes, axis=2)

    for iteration in range(num_rounds):
        # Calcular distancias al sink y niveles de los nodos
        dist_al_sink = np.linalg.norm(pos_nodes - sink_pos, axis=1)

        # Clasificación en niveles
        niveles = classify_levels(dist_al_sink, num_niveles)

        # Selección de Cluster Heads
        CH = select_cluster_heads(energia_nodos, niveles, threshold_bateria)

        # Verificar si se seleccionaron CHs suficientes
        if len(CH) == 0:
            print(f"No se seleccionaron Cluster Heads en la ronda {iteration + 1}.")
            continue  # Saltar a la siguiente ronda

        # Asociación de nodos a Cluster Heads
        idx_CH = assign_to_clusters(pos_nodes, pos_nodes[CH, :])

        # Verificar si la asignación fue exitosa
        if len(idx_CH) == 0:
            print(f"La asignación de nodos a Cluster Heads falló en la ronda {iteration + 1}.")
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

    # # print(node_uw[1]['NodeID'])
    # print('NeighboarSink : ', node_sink['NeighborCHs'])

    # for i in range(num_nodes):
    #     print('indice : ' , i , node_uw[i]['NodeID'], ' - ', node_uw[i]['ClusterHead'], ' - ', node_uw[i]['NumCluster'], ' : ', node_uw[i]['NeighborNodes'])

    ## EXPORTAR MAPA DEL CLUSTER
    # === Export map cluster (formal) ===
    # os.makedirs(output_dir, exist_ok=True)
    with open(os.path.join(output_dir,f"cluster_map_{RUN_ID}.csv"),
              "w",newline="") as f:
    # with open(f"stats/cluster_map_{RUN_ID}.csv","w",newline="") as f:
        w = csv.DictWriter(f, fieldnames=[
            "run_id","node_id","role","cluster_id","cluster_head","dist_to_sink_m","neighbor_count"
        ])
        w.writeheader()
        for i in range(num_nodes):
            node = node_uw[i]
            dist_sink = float(np.linalg.norm(node["Position"] - sink_pos))
            print(dist_sink)
            w.writerow({
                "run_id": RUN_ID,
                "node_id": node["NodeID"],
                "role": node["Role"],                 # 1=CH, 2=SN
                "cluster_id": node["NumCluster"],
                "cluster_head": node["ClusterHead"],
                "dist_to_sink_m": round(dist_sink, 2),
                "neighbor_count": len(node.get("NeighborNodes",[]))
            })
    ############################

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
    # from save_csv import save_stats_to_csv, save_stats_to_csv_cdma, save_stats_to_syn_csv

    # # Borrar la sincronización establecida
    # clear_sync_state(node_sink, node_uw, CH)

    ### SINCRONIZACIÓN DE NODO
    max_retries = 3
    timeout = 2
    # freq=20
    # processing_energy_cdma=5e-9
    # # alpha=1e-6
    # E_listen=5e-3
    # E_standby=2.5e-3

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
    # syn_packet = propagate_syn_to_CH_tdma(RUN_ID, node_sink, CH, node_uw, max_retries, timeout, E_schedule)
    propagate_syn_to_CH_tdma(RUN_ID, node_sink, CH, node_uw, max_retries, timeout, E_schedule)

    # print(" - ")
    # print('Resultados TDMA')

    # save_stats_to_csv_cdma('sync_stats_tdma.csv', stats_tdma, 'TDMA')
    # save_stats_to_syn_csv('sync_stats_tdma.csv', stats_tdma, 'TDMA')

    print("FIN PROCESO DE SINCRONIZACIÓN CON TDMA")
    print("-")


    ##
    ######################

    # %%    AUTENTICACIÓN CON TANGLE

    print("-")
    print("INCIO PROCESO DE AUTENTICACIÓN BASADO EN TX")

    from propagacionTx_light import propagate_tx_to_ch, authenticate_nodes_to_ch, propagate_tx_to_sink_and_cluster
    from tangle2_light import create_gen_block, delete_tangle, ingest_tx, confidence_confirm_tx
    import time
    # from save_csv import save_stats_tx, save_stats_energy_proTx_csv, save_stats_to_csv, save_stats_to_csv1, save_stats_to_csv2

    # Llamada a la función

    delete_tangle(node_sink, node_uw, CH)

    # Captura de estadisticas
    # Inicializar estadísticas
    # stats_tx = {
    #     "times_createTxgen": [],
    #     "times_verifyTx_toCH": [],
    #     "times_TxresponseCH": [],
    #     "times_propagation_txgen": [],
    #     "times_propagation_response_tx": [],
    # }

    # Crear la Tx genesis
    print("-")
    print ('AUTENTICACIÓN CON TANGLE...')

    rondas = 1

    for i in range(rondas):
        print('Ronda de calculo de creación y verificación de Tx : ', i+1)
        ####
        # Crear la genesis

        # print('Clave del sink : ', node_sink["PrivateKey_sign"])

        node_sink["PrivateKey_sign"]

        timestart = time.time() # inicio de la creación de tx genesis
        txgenesis = create_gen_block(RUN_ID, node_sink["NodeID"], node_sink["PrivateKey_sign"])
        time_createTX = time.time() - timestart

        # Se comenta 08/10/2025
        # node_sink["Tips"].append(txgenesis["ID"])   # Agrega la Tx genesis a la lista de tips
        # node_sink['Transactions'].append(txgenesis) # Agrega la Tx genesis a la lsita de Transactions
        # Nuevas lineas
        # Ingerir en el propio sink (autor de la génesis) y dejarla como tip
        ingest_tx(RUN_ID, node_sink, txgenesis, add_as_tip=True)

        # Confirmacion tx
        a,b,c = confidence_confirm_tx(RUN_ID, node_sink, txgenesis, M=20, theta=0.8,
                          alpha=0.3, max_steps=200, check_fresh=True,
                          log=True)

        print(a,b,c)
        time.sleep(10)
        
        # (opcional) LRU simple para no crecer sin límite
        node_sink["Tips"] = node_sink["Tips"][-128:]

        # print('Tiempo de creación de Tx genesis Sink: ', time_createTX)
        # print('Bloque genesis', txgenesis)
        # time.sleep(100)

        print("-")
        print ('PROPAGACIÓN DE LA TX GENESIS A LOS CH...')

        # txgenesis.setdefault("TS", time.time())
        # txgenesis.setdefault("TTL", 120.0)
        # txgenesis.setdefault("Nonce", hashlib.sha256(str(node_sink["NodeID"]).encode()+os.urandom(4)).hexdigest()[:16])
        # txgenesis.setdefault("Nonce1", ascon.hash((str(node_sink["NodeID"]) + str(time.time())).encode(), "Ascon-Hash", 32).hex()[:16])
        # node_sink["Tips"].append(txgenesis["ID"])
        # node_sink["Tips"] = node_sink["Tips"][-128:]  # LRU simple

        # # Capturar estadisticas
        # # Diccionario para capturar estadísticas individuales
        # stats_proTx = {
        #     "stats_proTx": {},  # Para guardar estadísticas por cada CH y nodo
        # }
        # stats_events = []
        # propagación de la tx genesis hacia los ch y nodos de cada cluster
        # en caso de recibir y verificar la tx genesis y verificarla la propaga hacia los nodos de su cluster
        # el ch prepara la tx de autenticación que la remite de vuelta al sink,el ch no se autentica mientras el sink
        #  no valide la tx de respuesta
        # Este proceso solo se lleva a cabo siempre y cuando los ch esten sincronizados.t
        # Sink -> CH
        # recived, end_time_verify = propagate_tx_to_ch(RUN_ID, node_sink, CH, node_uw, txgenesis, E_schedule, i)
        propagate_tx_to_ch(RUN_ID, node_sink, CH, node_uw, txgenesis, E_schedule, i)
        # stats_proTx["stats_proTx"].update(stats_proTx1)
        # print("Energia consumida hasta ahora : ", stats_proTx)
        # time.sleep(10)

        # Crear la tx de respuesta de los CH y transmitirlas al sink y los nodos del cluster
        # CH -> Sink
        # CH -> SN
        # end_time_responseCH, end_time_propagationTxCh = propagate_tx_to_sink_and_cluster(RUN_ID, node_sink, CH, node_uw, E_schedule, i)
        propagate_tx_to_sink_and_cluster(RUN_ID, node_sink, CH, node_uw, E_schedule, i)
        # stats_proTx["stats_proTx"].update(stats_proTx2)
        # print("Energia consumida hasta ahora : ", stats_proTx)
        # time.sleep(10)

        print("-")
        print('AUTENTICACIÓN DE LOS NODOS DEL CLUSTER')
        # Creación y propagación de la tx de autenticación de los nodos de cada cluster
        # SN -> CH
        authenticate_nodes_to_ch(RUN_ID, node_uw, CH, E_schedule, i)
        # stats_proTx["stats_proTx"].update(stats_proTx3)
        # print("Energia consumida hasta ahora : ", stats_proTx)
        # time.sleep(10)

        # ### Hacer un solo archivo
        # from collections import defaultdict

        # # Acumulador por nodo
        # acumulador = defaultdict(lambda: {"energy_consumed": 0.0})

        # # Iterar sobre cada stats dict
        # for partial in [stats_proTx1, stats_proTx2, stats_proTx3]:
        #     for nodo, valores in partial.items():
        #         acumulador[nodo]["energy_consumed"] += valores.get("energy_consumed", 0.0)

        # #   Asignar al campo global
        # stats_proTx["stats_proTx"] = dict(acumulador)

        # # 4. Procesar estadísticas
        # print("\n=== Estadísticas completas ===")
        # print("Consumo energía CH (Tx):", sum(stats4["energy"]["CH"]["tx"]))
        # print("Consumo energía CH (Rx):", sum(stats4["energy"]["CH"]["rx"]))
        # print("Consumo energía SN (Tx):", sum(stats4["energy"]["SN"]["tx"]))
        # print("Consumo energía SN (Rx):", sum(stats4["energy"]["SN"]["rx"]))
        # print("Tiempo promedio propagación:", np.mean(stats4["times"]["propagation"]))
        # print("Tiempo promedio propagación por CH:", np.mean(stats4["times"]["propagation_all"]))
        # print("Tiempo promedio verificación:", np.mean(stats4["times"]["verification"]))
        # print("Total reintentos:", stats4["attempts"])

        # 5. Guardar estadísticas en CSV
        # save_stats_to_csv(stats1, "estadisticas_simulacion1.csv")
        # save_stats_to_csv(stats2, "estadisticas_simulacion2.csv")
        # save_stats_to_csv(stats3, "estadisticas_simulacion3.csv")
        # save_stats_to_csv(stats4, "estadisticas_simulacion4.csv")

        # save_stats_to_csv1(stats1, "estadisticas_simulacion5.csv")
        # save_stats_to_csv2(stats_events, "estadisticas_TxAuth.csv")

        # Convertir las listas a cadenas para almacenarlas
        # time_verify_str = ','.join(map(str, end_time_verify))
        # time_response_str = ','.join(map(str, end_time_responseCH))

        # print('Tiempo de verificación de Tx genesis por CH or SN : ', end_time_verify)
        # print('Tiempo de creación de Tx response por CH or SN: ', end_time_responseCH)

        # stats_tx["times_createTxgen"].append(time_createTX)
        # stats_tx["times_propagation_txgen"].append(times_propagation_tx)
        # stats_tx["times_verifyTx_toCH"].append(end_time_verify)
        # stats_tx["times_TxresponseCH"].append(end_time_responseCH)
        # stats_tx["times_propagation_response_tx"].append(end_time_propagationTxCh)

    # save_stats_tx('stats_tx.csv', stats_tx)
    # print('Las estadisticas se almacenaron...')

    # al FINAL de la simulación
    from tangle_logger_light import flush_all
    flush_all()

    print("FIN PROCESO DE AUTENTICACIÓN BASADO EN TX")
    # ####

    # print('Nodo Sink : ', node_sink)


    #%%
    # from transmission_summary_uan import summarize_per_node, summarize_global

    ## INICIO PROCESO DE TRANSMISIÓN DE DATOS CIFRADOS CON ASCON
    print("-")
    print ('INICIO PROCESO DE TRANSMISIÓN DE DATOS CIFRADOS CON ASCON...')

    # from transmit_data_test import create_shared_keys_table, generate_shared_keys, transmit_data
    from transmit_data_light_uan import create_shared_keys_table, generate_shared_keys, transmit_data, encode_marine_payload

    # Se crea la tabla en la BBDD donde se van a crear las claves compartidas
    create_shared_keys_table("bbdd_keys_shared_sign_cipher.db")

    # 📌 Generar claves compartidas después de la autenticación
    generate_shared_keys("bbdd_keys_shared_sign_cipher.db", node_uw, CH, node_sink)

    # # Número total de transmisiones que queremos completar
    # total_transmissions = 20
    # completed_transmissions = 0  # Contador de transmisiones realizadas
    # max_attempts = 100  # Para evitar un bucle infinito si no hay nodos elegibles
    # attempts = 0

    # # Buffers para cada CH y tiempos de último envío
    # buffer_CH = {ch_id: [] for ch_id in CH}
    # ultimo_envio_CH = {ch_id: time.time() for ch_id in CH}

    # print("CHs : ", CH)
    # print("buffer_CH : ", buffer_CH)
    # print("ultimo_envio_CH", ultimo_envio_CH)

    # Parámetros realistas
    MAX_BUFFER = 5               # número máximo de datos antes de enviar al Sink
    AGGREGATION_TIMEOUT = 120     # segundos máximo antes de forzar envío

    # attempts = 0
    # while completed_transmissions < total_transmissions and attempts < max_attempts:
    #     attempts += 1  # Contador de intentos para evitar bucles infinitos

    #     # Seleccionamos un nodo aleatorio
    #     sender_index = np.random.randint(0, len(node_uw))  # Selección aleatoria de nodo
    #     sender = node_uw[sender_index]

    #     # Obtener el ID del Cluster Head (CH)
    #     # ch_id = sender.get("ClusterHead")
    #     ch_id = sender["ClusterHead"]
    #     # print("Sender : ", ch_id)

    #     # Validar que el nodo tiene un Cluster Head asignado
    #     if ch_id is None or ch_id == sender["NodeID"]:
    #         print("Detiene en caso de no tener CH asignado o es el mismo nodo...")
    #         continue  # Saltar si el nodo no tiene CH o si es su propio CH

    #     # Obtener el nodo Cluster Head
    #     receiver = node_uw[ch_id - 1]
    #     # print("Receiver : ", receiver["NodeID"])
    #     # time.sleep(1)

    #     # verificar que datos se envian
    #     # print(" Sender : ",sender["NodeID"],"-> Receiver : ", receiver["NodeID"])

    #     # Transmitir datos
    #     transmit_data("bbdd_keys_shared_sign_cipher.db", sender, receiver, f"Temperatura: {np.random.uniform(0, 30):.2f}°C")

    #     completed_transmissions += 1  # Incrementar transmisiones realizadas

    # # 📌 Simulación de CH enviando datos al Sink
    # for ch in CH:
    #     node_cluster = node_uw[ch]
    #     transmit_data("bbdd_keys_shared_sign_cipher.db", node_cluster, node_sink, "Datos agregados del cluster")

    # print(f"✅ Simulación completa: {completed_transmissions}/{total_transmissions} transmisiones realizadas.")

    ## cambiar a tiempo de transmisiones
    ##M Mirar el articulo con el que se vaya a comparar

    # # # while completed_transmissions < total_transmissions and attempts < max_attempts:
    # # #     attempts += 1
    # # #     sender_index = np.random.randint(0, len(node_uw))
    # # #     sender = node_uw[sender_index]
    # # #     ch_id = sender["ClusterHead"]

    # # #     if ch_id is None or ch_id == sender["NodeID"]:
    # # #         print("Detiene en caso de no tener CH asignado o es el mismo nodo...")
    # # #         continue

    # # #     receiver = node_uw[ch_id - 1]  # CH
    # # #     # distancia = np.linalg.norm(sender["Position"] - receiver["Position"])
    # # #     # t_prop = propagation_time(distancia,sender["Position"],receiver["Position"])

    # # #     # # Simular propagación
    # # #     # time.sleep(t_prop)

    # # #     # # Registrar energía
    # # #     # energia_tx = calcular_energia_paquete("data", es_tx=True)
    # # #     # energia_rx = calcular_energia_paquete("data", es_tx=False)

    # # #     # print("energia_tx : ", energia_tx," energia_rx : ", energia_rx)

    # # #     # print(sender)
    # # #     # print(receiver)

    # # #     # Transmisión simulada
    # # #     data_str = f"{np.random.uniform(0, 30):.2f}°C"
    # # #     transmit_data(RUN_ID, "bbdd_keys_shared_sign_cipher.db", sender, receiver, str(data_str), E_schedule, source='SN', dest='CH')

    # # #     print("CH_id : ", ch_id)
    # # #     # Almacenar en buffer del CH
    # # #     # transmit_data("bbdd_keys_shared_sign_cipher.db", sender, receiver, str(data_str), E_schedule, role="CH", process='des')
    # # #     buffer_CH[ch_id - 1].append(data_str)
    # # #     completed_transmissions += 1

    # # #     # Verificar si CH debe transmitir al Sink
    # # #     tiempo_desde_ultimo_envio = time.time() - ultimo_envio_CH[ch_id - 1]

    # # #     if len(buffer_CH[ch_id - 1]) >= MAX_BUFFER or tiempo_desde_ultimo_envio >= AGGREGATION_TIMEOUT:
    # # #         print("Envia el CH al Sink...")
    # # #         ch_node = node_uw[ch_id - 1]
    # # #         # distancia_sink = np.linalg.norm(ch_node["Position"] - node_sink["Position"])
    # # #         # t_prop_sink = propagation_time(distancia_sink,ch_node["Position"], node_sink["Position"])
    # # #         # time.sleep(t_prop_sink)

    # # #         datos_agregados = "; ".join(buffer_CH[ch_id - 1])
    # # #         transmit_data(RUN_ID, "bbdd_keys_shared_sign_cipher.db", ch_node, node_sink, datos_agregados, E_schedule, source='CH', dest='Sink')

    # # #         buffer_CH[ch_id - 1] = []  # Vaciar buffer
    # # #         ultimo_envio_CH[ch_id - 1] = time.time()

    # # # summarize_per_node()
    # # # summarize_global()


    # # Nuevo modelo de envio y rececpci+on de datos basado en tiempo
    # # =========================
    # # Simulación por TIEMPO (evento discreto) con filtros de Sync+Auth
    # # =========================

    # def _is_tx_allowed(node) -> bool:
    #     # Solo transmiten nodos sincronizados y autenticados
    #     return bool(node.get("IsSynced")) and bool(node.get("Authenticated"))

    # # Parámetros de tiempo (simulados)
    # SIM_DURATION_S = 60            # duración total de la simulación (p.ej., 10 min)
    # MEAN_INTERVAL_SN_S = 30         # media del intervalo (exponencial) entre envíos por SN
    # JITTER_BOOTSTRAP_S = 5          # pequeño desfase inicial aleatorio

    # # Buffers por CH (clave: NodeID del CH) y reloj simulado
    # buffer_CH = {ch_id: [] for ch_id in CH}
    # ultimo_envio_CH = {ch_id: 0.0 for ch_id in CH}   # tiempo simulado, no wall-clock
    # sim_now = 0.0
    # sim_end = SIM_DURATION_S


    # print("buffer_CH", buffer_CH)
    # print("ultimo_envio_CH", ultimo_envio_CH)

    # # SN candidatos (tienen CH asignado y no son su propio CH)
    # sn_indices = [
    #     i for i, n in enumerate(node_uw)
    #     if n.get("ClusterHead") not in (None, n["NodeID"])
    # ]

    # # Agenda de próximos envíos por SN (tiempo simulado)
    # next_send_time = {}
    # for i in sn_indices:
    #     next_send_time[i] = sim_now + np.random.uniform(0, JITTER_BOOTSTRAP_S) + np.random.exponential(MEAN_INTERVAL_SN_S)

    # print("next_send_time : ", next_send_time)

    # MAX_EVENTS = 100000
    # events_processed = 0

    # while sim_now < sim_end and events_processed < MAX_EVENTS and len(next_send_time) > 0:
    #     # 1) Elegir el próximo evento (SN con menor 'next_send_time')
    #     i_next = min(next_send_time, key=lambda k: next_send_time[k])
    #     t_event = next_send_time[i_next]

    #     if t_event > sim_end:
    #         break

    #     sim_now = t_event

    #     sender = node_uw[i_next]
    #     ch_id = int(sender["ClusterHead"])
    #     print("ch_id", ch_id)
    #     ch_node = node_uw[ch_id - 1]   # acceso por índice en node_uw
    #     # print("ch_node", ch_node)

    #     # 2) Verificar permisos de transmisión (SN y su CH)
    #     sn_ok = _is_tx_allowed(sender)
    #     ch_ok = _is_tx_allowed(ch_node)

    #     # Si el SN no está listo (sync+auth) o su CH no está listo para recibir, solo reprogramamos ese SN
    #     if not (sn_ok and ch_ok):
    #         next_send_time[i_next] = sim_now + np.random.exponential(MEAN_INTERVAL_SN_S)
    #         events_processed += 1
    #         continue

    #     # 3) Ejecutar envío SN -> CH
    #     data_str = f"{np.random.uniform(0, 30):.2f}°C"
    #     print("El SN envia datos al CH...")
    #     transmit_data(
    #         RUN_ID, "bbdd_keys_shared_sign_cipher.db",
    #         sender, ch_node, str(data_str),
    #         E_schedule, source='SN', dest='CH'
    #     )

    #     # 4) Agregar al buffer del CH (clave: NodeID del CH)
    #     buffer_CH[ch_id-1].append(data_str)

    #     # 5) ¿El CH debe enviar al Sink por tamaño o timeout? CH debe estar sync+auth
    #     if _is_tx_allowed(ch_node) and (
    #         len(buffer_CH[ch_id-1]) >= MAX_BUFFER or (sim_now - ultimo_envio_CH[ch_id-1]) >= AGGREGATION_TIMEOUT
    #     ):
    #         print("El CH envia datos al Sink...")
    #         datos_agregados = "; ".join(buffer_CH[ch_id-1])
    #         transmit_data(
    #             RUN_ID, "bbdd_keys_shared_sign_cipher.db",
    #             ch_node, node_sink, datos_agregados,
    #             E_schedule, source='CH', dest='Sink'
    #         )
    #         buffer_CH[ch_id-1] = []
    #         ultimo_envio_CH[ch_id-1] = sim_now

    #     # 6) Reagendar el próximo envío de ese SN
    #     next_send_time[i_next] = sim_now + np.random.exponential(MEAN_INTERVAL_SN_S)
    #     events_processed += 1

    # # Revisar
    # # # Flush final: solo CH sync+auth envían lo que quede en buffer
    # # for ch_id in CH:
    # #     if buffer_CH[ch_id]:
    # #         ch_node = node_uw[ch_id - 1]
    # #         if _is_tx_allowed(ch_node):
    # #             datos_agregados = "; ".join(buffer_CH[ch_id])
    # #             print("El CH envia datos al Sink en caso de quedar pendientes...")
    # #             transmit_data(
    # #                 RUN_ID, "bbdd_keys_shared_sign_cipher.db",
    # #                 ch_node, node_sink, datos_agregados,
    # #                 E_schedule, source='CH', dest='Sink'
    # #             )
    # #         buffer_CH[ch_id] = []
    # #         ultimo_envio_CH[ch_id] = sim_now

    # # Resúmenes
    # summarize_per_node()
    # summarize_global()

    #%%
    ## Otra forma de ejecutar la simulaión 
    # =========================
    # Parámetros de la simulación
    # =========================
    SEND_INTERVAL_S = 100           # intervalo fijo entre envíos SN -> CH
    # SIM_DURATION_S   = 3600         # ej: simulo 1h y proyecto a 24h
    SIM_DURATION_S   = 600         # ej: simulo 10 y proyecto a 24h
    # PROJECT_TO_24H   = True
    PROJECTION_REF_S = 24*3600      # 86400
    # PROJECTION_FACTOR = (PROJECTION_REF_S / SIM_DURATION_S) if PROJECT_TO_24H else 1.0
    PROJECTION_FACTOR = (PROJECTION_REF_S / SIM_DURATION_S)

    # projected_energy = total_energy * PROJECTION_FACTOR
    # projected_packets = total_tx * PROJECTION_FACTOR
    # projected_bits = d["bits_received"].sum() * PROJECTION_FACTOR

    JITTER_BOOTSTRAP_S = 5          # desfase inicial aleatorio pequeño
    MAX_BUFFER = 10
    AGGREGATION_TIMEOUT = 600       # todo en segundos de tiempo simulado

    def _is_tx_allowed(node) -> bool:
        return bool(node.get("IsSynced")) and bool(node.get("Authenticated"))

    # Buffers por CH (clave: NodeID del CH) y reloj simulado
    buffer_CH = {ch_id: [] for ch_id in CH}
    ultimo_envio_CH = {ch_id: 0.0 for ch_id in CH}  # tiempo SIMULADO
    sim_now = 0.0
    sim_end = SIM_DURATION_S

    # SN elegibles (tienen CH asignado distinto a sí mismos)
    sn_indices = [
        i for i, n in enumerate(node_uw)
        if n.get("ClusterHead") not in (None, n["NodeID"])
    ]

    # Agenda de próximos envíos (intervalo FIJO de 100s)
    next_send_time = {}
    for i in sn_indices:
        next_send_time[i] = sim_now + np.random.uniform(0, JITTER_BOOTSTRAP_S)

    # print("next_send_time : ", next_send_time)
    # time.sleep(10)

    MAX_EVENTS = 1_000_000
    events_processed = 0

    while sim_now < sim_end and events_processed < MAX_EVENTS and len(next_send_time) > 0:
        # 1) próximo evento
        i_next = min(next_send_time, key=lambda k: next_send_time[k])
        t_event = next_send_time[i_next]
        if t_event > sim_end:
            break
        sim_now = t_event

        sender = node_uw[i_next]
        ch_id = int(sender["ClusterHead"])
        ch_node = node_uw[ch_id - 1]

        # 2) filtro: solo SN y su CH si están sync + auth
        if not (_is_tx_allowed(sender) and _is_tx_allowed(ch_node)):
            # reprogramar este SN al siguiente intervalo
            next_send_time[i_next] = sim_now + SEND_INTERVAL_S
            events_processed += 1
            continue

        # 3) envío SN -> CH
        print("El SN envia datos al CH...")
        # data_str = f"{np.random.uniform(0, 30):.3f}"
        payload, (temp, salinity, pressure) = encode_marine_payload()

        # print("payload, (temp, salinity, pressure) : ", payload, (temp, salinity, pressure), "Tamaño binario del payload : ", len(payload))

        encrypted_msg = transmit_data(
            RUN_ID, "bbdd_keys_shared_sign_cipher.db", node_uw,
            sender, ch_node, str(payload),
            E_schedule, source='SN', dest='CH'
        )
        # encrypted_str = encrypted_msg.hex()
        # buffer_CH[ch_id-1].append(encrypted_str)
        buffer_CH[ch_id-1].append(payload)

        # 4) ¿CH -> Sink? solo si CH sync+auth y toca por buffer/timeout
        if _is_tx_allowed(ch_node) and (
            len(buffer_CH[ch_id-1]) >= MAX_BUFFER or (sim_now - ultimo_envio_CH[ch_id-1]) >= AGGREGATION_TIMEOUT
        ):
            print("El CH envia datos al Sink...")
            # datos_agregados = "; ".join(buffer_CH[ch_id-1])
            # datos_agregados = "; ".join(x.hex() for x in buffer_CH[ch_id-1])
            datos_agregados = b"".join(buffer_CH[ch_id-1])  # binario puro
            print("datos_agregados : ", datos_agregados, "len binarios: ", len(datos_agregados))

            # import base64
            # datos_agregados1 = "; ".join(base64.b64encode(x).decode('utf-8') for x in buffer_CH[ch_id-1])
            # print("datos_agregados1 : ", datos_agregados1)

            transmit_data(
                RUN_ID, "bbdd_keys_shared_sign_cipher.db", node_uw,
                ch_node, node_sink, datos_agregados,
                E_schedule, source='CH', dest='Sink'
            )
            buffer_CH[ch_id-1] = []
            ultimo_envio_CH[ch_id-1] = sim_now

        # 5) reagendar el mismo SN al próximo intervalo fijo
        next_send_time[i_next] = sim_now + SEND_INTERVAL_S
        events_processed += 1

    # # 6) flush final (lo que quede en buffers), solo CH sync+auth
    # for ch_id in CH:
    #     if buffer_CH[ch_id]:
    #         ch_node = node_uw[ch_id - 1]
    #         if _is_tx_allowed(ch_node):
    #             datos_agregados = "; ".join(buffer_CH[ch_id])
    #             transmit_data(
    #                 RUN_ID, "bbdd_keys_shared_sign_cipher.db", node_uw,
    #                 ch_node, node_sink, datos_agregados,
    #                 E_schedule, source='CH', dest='Sink'
    #             )
    #         buffer_CH[ch_id] = []
    #         ultimo_envio_CH[ch_id] = sim_now

    # Resumen y PROYECCIÓN
    # summarize_per_node()
    # summarize_global()

    print(f"\n--- Proyección a 24h ---")
    print(f"Ventana simulada: {SIM_DURATION_S/3600:.2f} h; factor F = {PROJECTION_FACTOR:.2f}")
    print("Multiplica: energía total, nº de paquetes y bits por F. Latencias por paquete NO se escalan.")

    from transmission_summary_uan import summarize_global_by_run, summarize_per_node_by_run

    #%%

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
    # current_dir = os.getcwd()
    current_dir = os.environ.get("OUTPUT_DIR", os.getcwd())

    # Definir la carpeta donde se encuentra la base de datos (carpeta 'save_struct')
    carpeta_destino = os.path.join(current_dir, 'save_struct')

    # Crea la carpeta en caso de no existir
    os.makedirs(carpeta_destino, exist_ok=True)

    # Obtener el run_id desde variable de entorno o parámetro
    run_id = os.environ.get("RUN", "run01")  # puedes usar str(run_num) si lo tienes como entero
    num_nodes = os.environ.get("UNSN_NUM_NODES", "20")  # puedes usar str(run_num) si lo tienes como entero

    # # Ruta completa del archivo de la base de datos dentro de la carpeta 'save_struct'
    # ruta_nodos = os.path.join(carpeta_destino, 'nodos_guardados.pkl')
    # ruta_sink = os.path.join(carpeta_destino, 'sink_guardado.pkl')
    # Rutas con nombre por run
    ruta_nodos = os.path.join(carpeta_destino, f'nodos_guardados_{run_id}_{num_nodes}.pkl')
    ruta_sink = os.path.join(carpeta_destino, f'sink_guardado_{run_id}_{num_nodes}.pkl')


    # Supongamos que node_uw es tu lista de nodos
    with open(ruta_nodos, 'wb') as file:
        pickle.dump(node_uw, file)

    # Guardamos el sink en un archivo para luego utilizarla
    with open(ruta_sink, 'wb') as file:
        pickle.dump(node_sink, file)

    print ('FIN PROCESO DE GUARDADO NODOS EN ARCHIVO PICKLE...')

    #################


if __name__ == "__main__":
    import os
    import argparse

    # jala el dir por num_nodes
    parser = argparse.ArgumentParser()
    parser.add_argument("--output_dir", type=str, default=None)
    args = parser.parse_args()
    os.environ["OUTPUT_DIR"] = args.output_dir or ""
    os.environ["UWSN_EVENTS_CSV"] = os.path.join(os.environ["OUTPUT_DIR"], "transmissions.csv")
    # os.environ["UWSN_ENERGY_INITIAL_J"] = "100.0"

    # Defaults si no te pasan nada
    RUN_NUM = int(os.environ.get("RUN", "1"))
    SEED    = int(os.environ.get("UWSN_SEED", "1337"))
    NUM_NODES = int(os.environ.get("UNSN_NUM_NODES", "20"))
    run_one(RUN_NUM, SEED, NUM_NODES, output_dir=args.output_dir)