# from test_throp import propagation_time, compute_path_loss, propagation_time1
from path_loss import compute_path_loss, propagation_time1
from noise_uan_aariza import compute_uan_noise
from curva_anclada_distancias_menores import p_tx_approx_W, p_tx_approx_W3000
import numpy as np
import time
import os


# Agregardo 02/10/2025
# === Perfil de cómputo (Raspberry Pi 3 B+, n=1000) ===
# Conmutador: usa 'median' (robusto) o 'mean' (promedio) como nominal
PROC_BASE = os.environ.get("UWSN_PROC_BASE", "median").lower().strip()  # 'median' | 'mean'

# Tiempos [s]
_MEAN = {
    "sign_s":            0.00046933,   # Ed25519 sign
    "verify_s":          0.00065230,   # Ed25519 verify
    "keygen_ed25519_s":  0.00255359,   # Ed25519 keygen
    "ecdh_x25519_s":     0.00052116,   # X25519 ECDH shared
    # Si mediste HKDF en esta misma campaña, reemplaza:
    "hkdf_s":            0.00022278,    # <- de tu tabla anterior (ajusta si tienes el nuevo)

    # Cambiar
    "encrypt_s":         0.00031245,    # tiempo medio de cifrado en segundos
    "descrypt_s":        0.00029812     # tiempo medio de descifrado en segundos
}

_MEDIAN = {
    "sign_s":            0.00045049,
    "verify_s":          0.00063753,
    "keygen_ed25519_s":  0.00264311,
    "ecdh_x25519_s":     0.00049949,
    "hkdf_s":            0.00021732,
    # cambiar
    "encrypt_s":         0.00030567, 
    "descrypt_s":        0.00029044
}

OPS_TIME = (_MEDIAN if PROC_BASE == "median" else _MEAN).copy()

# Potencia activa durante cómputo (SoC/MCU embebido; ajusta en metodología)
P_PROC = float(os.environ.get("UWSN_P_PROC_W", "0.10"))  # 0.10 W = 100 mW por defecto

def energy_proc_j(t_proc_s: float, p_proc=P_PROC) -> float:
    return max(0.0, float(p_proc) * max(0.0, float(t_proc_s)))

def estimate_proc_time_s(*, bits:int=0, do_enc=False, do_dec=False, do_hash=False,
                         do_sign=False, do_verify=False, do_ecdh=False, do_hkdf=False,
                         do_tips=False, override:dict=None) -> float:
    """
    Suma tiempos de operaciones a partir del perfil medido.
    'override' permite inyectar valores concretos por operación: {'verify_s':0.00063,...}
    """
    t = 0.0
    o = override or {}
    if do_sign:   t += o.get("sign_s",   OPS_TIME["sign_s"])
    if do_verify: t += o.get("verify_s", OPS_TIME["verify_s"])
    if do_ecdh:   t += o.get("ecdh_x25519_s", OPS_TIME["ecdh_x25519_s"])
    if do_hkdf:   t += o.get("hkdf_s",   OPS_TIME["hkdf_s"])
    # si modelas DAG/tips como coste lógico (no cripto pura):
    if do_tips:   t += o.get("tips_s", 0.003)
    if do_enc:   t += o.get("encrypt_s",   OPS_TIME["encrypt_s"])
    if do_dec:   t += o.get("descrypt_s",   OPS_TIME["descrypt_s"])
    # si más adelante se añade ASCON medido, puedes sumar aquí enc/dec/hash
    return t
####

# # Parámetros físicos y energéticos
# # EvoLogics S2CR 15/27 de acuerdo a documento 2016
# P_TX_MAX = 65      # Potencia de consumo en transmisión (W)
# P_TX_6000 = 15     # Potencia de consumo en transmisión (W)
# P_TX_3000 = 5      # Potencia de consumo en transmisión (W)
# P_TX_1500 = 2.5    # Potencia de consumo en transmisión (W)
# P_RX = 0.8         # Potencia de consumo de recepción (W)
# R_B = 9200         # Bitrate en bps

# TX_LEVELS = [
#     (1500,  2.5),   # hasta 1500 m → 2.5 W
#     (3000,  5.0),   # hasta 3000 m → 5 W
#     (6000, 15.0),   # hasta 6000 m → 15 W
#     (np.inf, 65.0)  # más de 6000 m → 65 W
# ]

# def consumo_tx_por_distancia(distance_m: float) -> float:
#     for max_dist, power_W in TX_LEVELS:
#         if distance_m <= max_dist:
#             return power_W
#     return 65.0

# Potencias de consumo para modos pasivos
P_STANDBY = 0.0025  # W (2.5 mW)
P_LISTEN = 0.005     # W (modo escucha/idle)

# Energía de programación por bit
E_SCHEDULE = 5e-9   # J/bit

## add
def consumo_tx_por_distancia_suavizado(distance_m: float) -> float:
    """
    Potencia de transmisión suavizada para d ≤ 1500 m,
    basada en modelo físico anclado a 2.5 W @ 1500 m.
    Para distancias mayores, usa el modelo escalonado original.
    """
    if distance_m <= 1500:
        return p_tx_approx_W(distance_m)
    elif distance_m <= 3000:
        return p_tx_approx_W3000(distance_m)
    elif distance_m <= 6000:
        return p_tx_approx_W3000(distance_m)
    else:
        raise ValueError(f"Distancia fuera de rango: {distance_m} m")
##

def calcular_energia_paquete(tipo_paquete, distance_m, es_tx=True):
    """
    Calcula la energía para transmitir o recibir un paquete según su tipo y tamaño.

    Parámetros:
    tipo_paquete: str, puede ser "sync", "control", "data", "agg"
    es_tx: bool, True si es transmisión, False si es recepción

    Retorna:
    Energía estimada en julios.
    """
    # Parámetros base
    # potencia_tx = 2.5        # W
    # potencia_tx = consumo_tx_por_distancia(distance_m)
    potencia_tx = consumo_tx_por_distancia_suavizado(distance_m)
    potencia_rx = 0.8       # W
    bitrate = 9200          # bps

    # Tamaños típicos
    tamanos = {
        "sync": 7 * 8,      # 7 Bytes
        "tx": 185 * 8,      # 185 Bytes
        "data": 48 * 8,     # 48 Bytes
        "agg": 201 * 8,     # 201 Bytes
        "ack": 7 * 8        # 7 Bytes
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
    elif "ACK" in mensaje or "ack" in mensaje.lower():
        return "ack"
    else:
        return "none"  # Por defecto sin definición


# Función para calcular el timeout para los tiempos de guarda
# Timeout = t{prop} + t{tx} + t{proc} + margen
# t{prop} = d{max}/v
# t{tx} = L/R
# t{proc} = 0.01 - 0.05 s (depende del hadware)
# Margen 20 - 30% del tiempo estimado
## “Se aplica un margen del 30% sobre la suma de propagación, transmisión y procesamiento, para cubrir variabilidad ambiental, jitter de hardware y efectos Doppler en entornos submarinos.”

def calculate_timeout(sink_pos, ch_pos, bitrate=9200, packet_size=72, proc_time_s=None):
    # # Calcular distancia máxima al CH más lejano
    dist = np.linalg.norm(sink_pos - ch_pos)    # se debe comentar 10/09/2025
    # t_prop = dist / 1500  # Velocidad del sonido ≈ 1500 m/s

    # t_prop = propagation_time(dist, sink_pos, ch_pos)   # se comenta 10/09/2025 # segundos(s)
    lat_prop = propagation_time1(sink_pos, ch_pos, depth=None, region="standard")

    # Tiempo de transmisión # segundos(s)
    lat_tx = packet_size / bitrate

    # Tiempo de procesamiento (empírico)
    lat_proc = (proc_time_s if (proc_time_s is not None) else 0.020)  # s, por defecto 20 ms

    # Margen de seguridad (30% - 50%)
    margin = 0.3 * (lat_prop + lat_tx + lat_proc)

    return lat_prop*1000, lat_tx*1000, lat_proc*1000, lat_prop + lat_tx + lat_proc + margin

# # Uso en propagate_syn_to_CH_tdma
# timeout = calculate_timeout(sink["Position"], node_uw[ch]["Position"])


def update_energy_standby_others(all_nodes, active_ids, t_interval_s, verbose=False):
    """
    Actualiza la energía de los nodos que no están activos (ni transmitiendo ni recibiendo)
    durante un intervalo de tiempo t_interval_s (en segundos).

    Parámetros:
    - all_nodes: lista de diccionarios de nodos
    - active_ids: lista de IDs de nodos activos (ej. [tx_id, rx_id])
    - t_interval_s: duración del evento en segundos
    """
    for node in all_nodes:
        if node["NodeID"] not in active_ids:
            E_standby = energy_standby(t_interval_s)
            node["ResidualEnergy"] = max(node["ResidualEnergy"] - E_standby, 0)
            if verbose:
                print(f"[STANDBY] Nodo {node['NodeID']} consumió {E_standby:.6f} J | Residual: {node['ResidualEnergy']:.6f} J")
    return all_nodes


# Función para actualizar la energía de un nodo basado en su distancia al CH o Sink
def update_energy_node_tdma(node, target_pos, E_schedule, timeout, type_packet, role="SN", action="tx", verbose=False, t_verif_s=0.0):
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

    # guard_time = propagation_time(dist, node["Position"], target_pos)   # se comenta 10/09/2025
    ## “El guard time representa el tiempo previo a la recepción, necesario para compensar la propagación acústica y evitar colisiones. 
    # El timeout representa el tiempo posterior al evento, durante el cual el nodo permanece en modo escucha esperando confirmación o cierre del slot.”
    # 1) guard_time por propagación
    guard_time = propagation_time1(node["Position"], target_pos, depth=None, region="standard")

    # 2) energía de TX/RX
    # Calcular distancia y tiempo de propagación (guard_time)
    dist = np.linalg.norm(node["Position"] - target_pos)    # se debe comentar 10/09/2025
    # Energía según acción
    if action == "tx":
        E_tx = calcular_energia_paquete(type_packet, dist, es_tx=True)
        if role == "CH":
            E_sched = E_schedule
    elif action == "rx":
        E_rx = calcular_energia_paquete(type_packet, dist, es_tx=False)

    # Energía en escucha o standby (según rol)
    # 3) pasivo (listen/standby) durante guard y timeout
    if role in ["CH", "Sink"]:
        E_guard = energy_listen(guard_time)
        E_timeout = energy_listen(timeout)
    else:
        E_guard = energy_standby(guard_time)
        E_timeout = energy_listen(timeout)

    # Total energía
    # ... después de E_tx, E_rx, E_guard, E_timeout, E_sched
    # 4) cómputo
    E_proc = energy_proc_j(t_verif_s) if t_verif_s and t_verif_s > 0 else 0.0

    # 5) total y actualización
    # E_total = E_tx + E_rx + E_guard + E_timeout + E_sched
    E_total = E_tx + E_rx + E_guard + E_timeout + E_sched + E_proc
    node["ResidualEnergy"] = max(node["ResidualEnergy"] - E_total, 0)

    if verbose:
        print(f"[{role}-{action}] TX:{E_tx:.6f} RX:{E_rx:.6f} Guard:{E_guard:.6f} Timeout:{E_timeout:.6f} "
              f"Sched:{E_sched:.2e} Proc:{E_proc:.6f}  → Total:{E_total:.6f} J  | Residual:{node['ResidualEnergy']:.6f} J")
        
    # if verbose:
    #     print(f"[{role} - {action.upper()}] TX: {E_tx:.6f}, RX: {E_rx:.6f}, Guard: {E_guard:.6f}, Timeout: {E_timeout:.6f}, Schedule: {E_sched:.2e}")
    #     print(f"→ Total: {E_total:.6f} J | Residual: {node['ResidualEnergy']:.6f} J")

    return node


def update_energy_failed_rx(node, target_pos, timeout, role="SN", verbose=False):
    """
    Actualiza la energía de un nodo que intentó recibir un paquete pero no lo recibió (fallo por PER).
    Se considera energía de escucha activa (guard + timeout), sin procesamiento.
    Parámetros:
    - node: diccionario del nodo
    - target_pos: posición del transmisor
    - timeout: duración del evento en segundos
    - role: "SN", "CH", o "Sink"
    """
    guard_time = propagation_time1(node["Position"], target_pos, depth=None, region="standard")
    if role in ["CH", "Sink"]:
        E_guard = energy_listen(guard_time)
        E_timeout = energy_listen(timeout)
    else:
        E_guard = energy_standby(guard_time)
        E_timeout = energy_listen(timeout)

    E_total = E_guard + E_timeout
    node["ResidualEnergy"] = max(node["ResidualEnergy"] - E_total, 0)
    if verbose:
        print(f"[{role}-FAILED_RX] Guard:{E_guard:.6f} Timeout:{E_timeout:.6f} → Total:{E_total:.6f} J | Residual:{node['ResidualEnergy']:.6f} J")

    return node

# distancias_m = [1, 10, 100, 300, 500, 700, 1000, 1500, 2000, 3000]

# print("Distancia (m) | Potencia Tx (W)")
# print("-------------------------------")
# for d in distancias_m:
#     p_tx = consumo_tx_por_distancia_suavizado(d)
#     print(f"{d:>12} | {p_tx:>13.6f}")



#####
# # # Función para actualizar la energía de un nodo basado en su distancia al CH o Sink
# # def update_energy_node_tdma1(node, target_pos, E_schedule, timeout, type_packet, is_ch=False):
# #     """
# #     Actualiza la energía del nodo considerando su rol (CH o SN) en TDMA.
# #     Parámetros:
# #     - node: Diccionario con los datos del nodo (incluye Position y ResidualEnergy)
# #     - target_pos: Posición del objetivo (Sink para CHs, CH para SNs)
# #     - is_ch: Booleano que indica si el nodo es Cluster Head
# #     - E_schedule: Energía de programación TDMA (solo para CHs)
# #     - timeout: Tiempo máximo de espera para ACK

# #     Retorna:
# #     - El nodo con su energía residual actualizada
# #     """

# #     # # 3. Margen científico (3 componentes) para el calculo de Guard_time
# #     # jitter_margin = 0.01  # 10 ms (jitter de hardware)
# #     # doppler_margin = 0.02 * delta_dist/v_sound  # Efecto Doppler (2%)
# #     # safety_margin = 0.03  # 30 ms adicionales

# #     # 1. Calcular distancia y tiempo de propagación (guard_time)
# #     dist = np.linalg.norm(node["Position"] - target_pos)    # se debe comentar 10/09/2025

# #     # guard_time = propagation_time(dist, node["Position"], target_pos)   # se comenta

# #     guard_time = propagation_time1(node["Position"], target_pos, depth=None, region="standard")

# #     # 2. Calcular energía de transmisión según rol
# #     if is_ch:
# #         # CH: energía de tx + scheduling TDMA
# #         Et = calcular_energia_paquete(type_packet, dist, es_tx=True) + E_schedule
# #     else:
# #         # SN: solo energía de tx
# #         Et = calcular_energia_paquete(type_packet, dist, es_tx=True)

# #     # 3. Energía de recepción (igual para CH y SN)
# #     Er = calcular_energia_paquete(type_packet, dist, es_tx=False)

# #     # 4. Energía durante tiempos muertos
# #     if is_ch:
# #         # CH gasta energía en escucha (listen) durante guard_time y timeout
# #         E_guard = energy_listen(guard_time)
# #         E_timeout = energy_listen(timeout)
# #     else:
# #         # SN gasta energía en standby durante guard_time y escucha durante timeout
# #         E_guard = energy_standby(guard_time)
# #         E_timeout = energy_listen(timeout)

# #     # 5. Actualizar energía total
# #     energy_consumed = Et + Er + E_guard + E_timeout
# #     print("Energia consumida : ", energy_consumed, "E_guard : ", E_guard, "E_timeout : ", E_timeout)
# #     #time.sleep(5)

# #     node["ResidualEnergy"] = max(node["ResidualEnergy"] - energy_consumed, 0)  # No negativa

# #     return node


# # def calculate_guard_time(cluster_nodes, ch_pos):
# #     """
# #     Calcula el guard_time variable para un cluster submarino.

# #     Args:
# #         cluster_nodes: Lista de nodos en el cluster
# #         ch_pos: Posición del CH
# #         temp, salinity, depth: Parámetros ambientales

# #     Returns:
# #         guard_time en segundos
# #     """
# #     # 1. Calcular dispersión de retardos
# #     distances = [np.linalg.norm(node["Position"] - ch_pos) for node in cluster_nodes]
# #     delta_dist = max(distances) - min(distances)

# #     # 2. Obtener velocidad del sonido
# #     v_sound = 1449.2 + 4.6*temp - 0.055*temp**2 + 0.00029*temp**3 + \
# #               (1.34 - 0.01*temp)*(salinity - 35) + 0.016*depth

# #     # 3. Margen científico (3 componentes)
# #     jitter_margin = 0.01  # 10 ms (jitter de hardware)
# #     doppler_margin = 0.02 * delta_dist/v_sound  # Efecto Doppler (2%)
# #     safety_margin = 0.03  # 30 ms adicionales

# #     guard_time = (delta_dist / v_sound) + jitter_margin + doppler_margin + safety_margin

# #     return max(guard_time, 0.05)  # Mínimo 50 ms