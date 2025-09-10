from test_throp import propagation_time, compute_path_loss, propagation_time1
import numpy as np
import time

# Parámetros físicos y energéticos
# EvoLogics S2CR 15/27
P_TX = 65          # Potencia de transmisión (W)
P_RX = 0.8         # Potencia de recepción (W)
R_B = 9200         # Bitrate en bps

# Potencias para modos pasivos
P_STANDBY = 0.0025  # W (2.5 mW)
P_LISTEN = 0.05     # W (modo escucha/idle)

# Energía de programación por bit
E_SCHEDULE = 5e-9   # J/bit

def calcular_energia_paquete(tipo_paquete, es_tx=True):
    """
    Calcula la energía para transmitir o recibir un paquete según su tipo y tamaño.

    Parámetros:
    tipo_paquete: str, puede ser "sync", "control", "data", "agg"
    es_tx: bool, True si es transmisión, False si es recepción

    Retorna:
    Energía estimada en julios.
    """
    # Parámetros base
    potencia_tx = 65        # W
    potencia_rx = 0.8       # W
    bitrate = 9200          # bps

    # Tamaños típicos
    tamanos = {
        "sync": 6 * 8,      # 6 Bytes
        "tx": 200 * 8,      # 200 Bytes
        "data": 71 * 8,     # 71 Bytes
        "agg": 520 * 8,     # 520 Bytes
        "ack": 6 * 8        # 6 Bytes
    }

    if tipo_paquete not in tamanos:
        raise ValueError("Tipo de paquete desconocido.")

    bits = tamanos[tipo_paquete]
    tiempo = bits / bitrate  # duración del envío

    potencia = potencia_tx if es_tx else potencia_rx
    energia = potencia * tiempo
    return energia

def energy_listen(t_escucha_s):
    return P_LISTEN * t_escucha_s

def energy_standby(t_standby_s):
    return P_STANDBY * t_standby_s


def obtener_tipo_paquete(mensaje):
    """
    Detecta el tipo de paquete a partir del contenido o metadatos.
    """
    if "SYN" in mensaje or "sync" in mensaje.lower():
        return "sync"
    elif "TRANSACTION" in mensaje or "Tx" in mensaje.lower():
        return "tx"
    elif "Temperatura" in mensaje or "Data:" in mensaje:
        return "data"
    elif "AGGREGATED" in mensaje or "agg" in mensaje.lower():
        return "agg"
    else:
        return "none"  # Por defecto sin definición


# Función para calcular el timeout para los tiempos de guarda
# Timeout = t{prop} + t{tx} + t{proc} + margen
# t{prop} = d{max}/v
# t{tx} = L/R
# t{proc} = 0.01 - 0.05 s (depende del hadware)
# Margen 20 - 30% del tiempo estimado
def calculate_timeout(sink_pos, ch_pos, bitrate=9200, packet_size=48):
    # # Calcular distancia máxima al CH más lejano
    dist = np.linalg.norm(sink_pos - ch_pos)    # se debe comentar 10/09/2025
    # t_prop = dist / 1500  # Velocidad del sonido ≈ 1500 m/s

    # t_prop = propagation_time(dist, sink_pos, ch_pos)   # se comenta 10/09/2025
    t_prop = propagation_time1(sink_pos, ch_pos)
    
    # Tiempo de transmisión
    t_tx = packet_size / bitrate
    
    # Tiempo de procesamiento (empírico)
    t_proc = 0.02
    
    # Margen de seguridad (30% - 50%)
    margin = 0.3 * (t_prop + t_tx + t_proc)
    
    return t_prop + t_tx + t_proc + margin

# # Uso en propagate_syn_to_CH_tdma
# timeout = calculate_timeout(sink["Position"], node_uw[ch]["Position"])


# def calculate_guard_time(cluster_nodes, ch_pos):
#     """
#     Calcula el guard_time variable para un cluster submarino.
    
#     Args:
#         cluster_nodes: Lista de nodos en el cluster
#         ch_pos: Posición del CH
#         temp, salinity, depth: Parámetros ambientales
        
#     Returns:
#         guard_time en segundos
#     """
#     # 1. Calcular dispersión de retardos
#     distances = [np.linalg.norm(node["Position"] - ch_pos) for node in cluster_nodes]
#     delta_dist = max(distances) - min(distances)
    
#     # 2. Obtener velocidad del sonido
#     v_sound = 1449.2 + 4.6*temp - 0.055*temp**2 + 0.00029*temp**3 + \
#               (1.34 - 0.01*temp)*(salinity - 35) + 0.016*depth
    
#     # 3. Margen científico (3 componentes)
#     jitter_margin = 0.01  # 10 ms (jitter de hardware)
#     doppler_margin = 0.02 * delta_dist/v_sound  # Efecto Doppler (2%)
#     safety_margin = 0.03  # 30 ms adicionales
    
#     guard_time = (delta_dist / v_sound) + jitter_margin + doppler_margin + safety_margin
    
#     return max(guard_time, 0.05)  # Mínimo 50 ms




# Función para actualizar la energía de un nodo basado en su distancia al CH o Sink
def update_energy_node_tdma(node, target_pos, E_schedule, timeout, type_packet, role="SN", action="tx", verbose=False):
    """
    Actualiza la energía del nodo considerando su rol (CH o SN) en TDMA.
    Parámetros:
    - node: Diccionario con los datos del nodo (incluye Position y ResidualEnergy)
    - target_pos: Posición del objetivo (Sink para CHs, CH para SNs)
    - is_ch: Booleano que indica si el nodo es Cluster Head
    - E_schedule: Energía de programación TDMA (solo para CHs)
    - timeout: Tiempo máximo de espera para ACK
    
    Retorna:
    - El nodo con su energía residual actualizada
    """
    
    # # 3. Margen científico (3 componentes) para el calculo de Guard_time
    # jitter_margin = 0.01  # 10 ms (jitter de hardware)
    # doppler_margin = 0.02 * delta_dist/v_sound  # Efecto Doppler (2%)
    # safety_margin = 0.03  # 30 ms adicionales
    
    # Inicialización
    E_tx = E_rx = E_sched = 0

    # 1. Calcular distancia y tiempo de propagación (guard_time)
    dist = np.linalg.norm(node["Position"] - target_pos)    # se debe comentar 10/09/2025

    # guard_time = propagation_time(dist, node["Position"], target_pos)   # se comenta 10/09/2025
    
    guard_time = propagation_time1(node["Position"], target_pos)

    # Energía según acción
    if action == "tx":
        E_tx = calcular_energia_paquete(type_packet, es_tx=True)
        if role == "CH":
            E_sched = E_schedule
    elif action == "rx":
        E_rx = calcular_energia_paquete(type_packet, es_tx=False)

    # Energía en escucha o standby (según rol)
    if role in ["CH", "Sink"]:
        E_guard = energy_listen(guard_time)
        E_timeout = energy_listen(timeout)
    else:
        E_guard = energy_standby(guard_time)
        E_timeout = energy_listen(timeout)
    
    # Total energía
    E_total = E_tx + E_rx + E_guard + E_timeout + E_sched
    node["ResidualEnergy"] = max(node["ResidualEnergy"] - E_total, 0)

    if verbose:
        print(f"[{role} - {action.upper()}] TX: {E_tx:.6f}, RX: {E_rx:.6f}, Guard: {E_guard:.6f}, Timeout: {E_timeout:.6f}, Schedule: {E_sched:.6f}")
        print(f"→ Total: {E_total:.6f} J | Residual: {node['ResidualEnergy']:.6f} J")
    
    return node


# Función para actualizar la energía de un nodo basado en su distancia al CH o Sink
def update_energy_node_tdma1(node, target_pos, E_schedule, timeout, type_packet, is_ch=False):
    """
    Actualiza la energía del nodo considerando su rol (CH o SN) en TDMA.
    Parámetros:
    - node: Diccionario con los datos del nodo (incluye Position y ResidualEnergy)
    - target_pos: Posición del objetivo (Sink para CHs, CH para SNs)
    - is_ch: Booleano que indica si el nodo es Cluster Head
    - E_schedule: Energía de programación TDMA (solo para CHs)
    - timeout: Tiempo máximo de espera para ACK
    
    Retorna:
    - El nodo con su energía residual actualizada
    """
    
    # # 3. Margen científico (3 componentes) para el calculo de Guard_time
    # jitter_margin = 0.01  # 10 ms (jitter de hardware)
    # doppler_margin = 0.02 * delta_dist/v_sound  # Efecto Doppler (2%)
    # safety_margin = 0.03  # 30 ms adicionales

    # 1. Calcular distancia y tiempo de propagación (guard_time)
    dist = np.linalg.norm(node["Position"] - target_pos)    # se debe comentar 10/09/2025

    # guard_time = propagation_time(dist, node["Position"], target_pos)   # se comenta
    
    guard_time = propagation_time1(node["Position"], target_pos)

    # 2. Calcular energía de transmisión según rol
    if is_ch:
        # CH: energía de tx + scheduling TDMA
        Et = calcular_energia_paquete(type_packet, es_tx=True) + E_schedule
    else:
        # SN: solo energía de tx
        Et = calcular_energia_paquete(type_packet, es_tx=True)
    
    # 3. Energía de recepción (igual para CH y SN)
    Er = calcular_energia_paquete(type_packet, es_tx=False)
    
    # 4. Energía durante tiempos muertos
    if is_ch:
        # CH gasta energía en escucha (listen) durante guard_time y timeout
        E_guard = energy_listen(guard_time)
        E_timeout = energy_listen(timeout)
    else:
        # SN gasta energía en standby durante guard_time y escucha durante timeout
        E_guard = energy_standby(guard_time)
        E_timeout = energy_listen(timeout)
    
    # 5. Actualizar energía total
    energy_consumed = Et + Er + E_guard + E_timeout
    print("Energia consumida : ", energy_consumed, "E_guard : ", E_guard, "E_timeout : ", E_timeout)
    #time.sleep(5)

    node["ResidualEnergy"] = max(node["ResidualEnergy"] - energy_consumed, 0)  # No negativa
    
    return node
