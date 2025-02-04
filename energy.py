def energia_nodo_normal(E_tx, S, b):
    tiempo_tx = S / b  # Tiempo de transmisión
    energia = E_tx * tiempo_tx  # Energía en Joules
    return energia

def energia_cluster_head(N, S, b, t_guarda, E_rx):
    tiempo_por_nodo = (S / b) + t_guarda  # Tiempo por nodo (TX + guarda)
    tiempo_total = N * tiempo_por_nodo    # Tiempo total en RX
    energia = E_rx * tiempo_total          # Energía en Joules
    return energia

# Parámetros de ejemplo
E_tx = 0.1   # 0.1 W (100 mW) en TX
E_rx = 0.05  # 0.05 W (50 mW) en RX
S = 1024     # bits por paquete
b = 1000     # 1000 bps
t_guarda = 0.01  # 10 ms de guarda por slot
N = 10       # 10 nodos en el clúster

# Calcular energías
energia_normal = energia_nodo_normal(E_tx, S, b)
energia_ch = energia_cluster_head(N, S, b, t_guarda, E_rx)

print(f"Energía por nodo normal: {energia_normal:.3f} J")
print(f"Energía del CH: {energia_ch:.3f} J")


def energia_cluster_head_CDMA(N, S, b, E_rx):
    tiempo_por_nodo = S / b           # Tiempo de recepción por paquete
    tiempo_total = N * tiempo_por_nodo # Tiempo total (señales simultáneas)
    energia = E_rx * tiempo_total      # Energía en Joules
    return energia

# # Parámetros (mismos que antes)
# E_rx = 0.05  # 0.05 W (50 mW)
# S = 1024     # bits
# b = 1000     # 1000 bps
# N = 10       # 10 nodos

# Calcular energía del CH con CDMA
energia_ch_cdma = energia_cluster_head_CDMA(N, S, b, E_rx)

print(f"Energía del CH con CDMA: {energia_ch_cdma:.3f} J")