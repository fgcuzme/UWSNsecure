
# Parámetros físicos y energéticos
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
        "agg": 520 * 8      # 520 Bytes
    }

    if tipo_paquete not in tamanos:
        raise ValueError("Tipo de paquete desconocido.")

    bits = tamanos[tipo_paquete]
    tiempo = bits / bitrate  # duración del envío

    potencia = potencia_tx if es_tx else potencia_rx
    energia = potencia * tiempo
    return energia

def energia_escucha(t_escucha_s):
    return P_LISTEN * t_escucha_s

def energia_standby(t_standby_s):
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
