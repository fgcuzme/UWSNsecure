import numpy as np

# Proceso de cluster basado en el estudio de "A Cluster-head Selection Scheme for Underwater Acoustic Sensor Networks"
# Guangsong Yang, School of Information Engineering, Jimei University, Xiamen, China, gsyang@jmu.edu.cn
# 2010

def classify_levels(dist_al_sink, num_levels):
    """
    Clasifica los nodos en niveles basados en la distancia al Sink.
    Los nodos más cercanos al Sink obtienen un nivel más bajo.
    Parámetros:
    dist_al_sink: array con las distancias de los nodos al Sink.
    num_levels: número de niveles a generar.
    Retorna:
    niveles: array con los niveles asignados a cada nodo, donde el nivel está basado en la distancia al Sink.
    """
    
    # Ordenar las distancias de menor a mayor
    indices = np.argsort(dist_al_sink)
    
    # Definir límites para cada nivel en función del rango de distancias
    dist_min = np.min(dist_al_sink)
    dist_max = np.max(dist_al_sink)
    niveles_limites = np.linspace(dist_min, dist_max, num_levels + 1)
    
    # Inicializar los niveles
    niveles = np.zeros(len(dist_al_sink), dtype=int)
    
    # Asignar los niveles a los nodos en función de las distancias
    for i in range(num_levels):
        if i < num_levels - 1:
            # Asignar nodos que caen dentro de cada rango
            niveles[np.where((dist_al_sink >= niveles_limites[i]) & (dist_al_sink < niveles_limites[i+1]))] = i + 1
        else:
            # Asegurar que cualquier nodo restante (el más lejano) se asigne al último nivel
            niveles[np.where(dist_al_sink >= niveles_limites[i])] = i + 1
    
    return niveles

# Ejemplo de uso en Python
# dist_al_sink = np.array([100, 200, 150, 500, 300])
# num_levels = 3
# niveles = classify_levels(dist_al_sink, num_levels)
# print(niveles)

import numpy as np

def select_cluster_heads(energia_nodos, niveles, threshold_bateria):
    """
    Selección de Cluster Heads basada en la métrica de tiempo.
    
    Parámetros:
    energia_nodos: array con las energías de los nodos.
    niveles: array con los niveles de los nodos (más bajos = más cercanos al Sink).
    threshold_bateria: umbral mínimo de batería para considerar un nodo elegible.

    Retorna:
    CH: array con los índices de los nodos seleccionados como Cluster Heads (CH).
    """
    
    E_init = np.max(energia_nodos)  # Energía inicial máxima
    N = len(energia_nodos)  # Número de nodos
    
    # Ajuste dinámico del umbral de energía mínima en el nivel 1
    energia_minima_nivel_1 = np.min(energia_nodos[niveles == 1])  # Energía mínima en el nivel 1
    if energia_minima_nivel_1 < threshold_bateria:
        threshold_bateria = energia_minima_nivel_1 + 0.1  # Ajusta el umbral para evitar nodos con energía muy baja

    # Inicializar el array de tiempos de espera
    tiempo_espera = np.full(N, np.inf)  # Inicializar con "inf" para nodos no elegibles

    # Calcular la métrica de tiempo de espera para cada nodo
    for i in range(N):
        if energia_nodos[i] > threshold_bateria:
            # Métrica de tiempo modificada para incluir el factor aleatorio que evita colisiones
            tiempo_espera[i] = (1 - energia_nodos[i] / E_init) * N + niveles[i] + np.random.rand()

    # Ordenar los nodos por tiempo de espera (menor es mejor)
    idx = np.argsort(tiempo_espera)

    # Seleccionar un número dinámico de CHs basado en los nodos y su energía promedio
    num_ch = round(0.05 * N + 0.05 * np.mean(energia_nodos))  # Ajuste dinámico
    CH = idx[:num_ch]  # Seleccionar los primeros num_ch nodos con menor tiempo de espera

    return CH

# Ejemplo de uso en Python:
# energia_nodos = np.array([0.8, 0.9, 0.5, 0.6, 0.7])
# niveles = np.array([1, 2, 2, 1, 3])
# threshold_bateria = 0.4
# CH = select_cluster_heads(energia_nodos, niveles, threshold_bateria)
# print(CH)


import numpy as np
from scipy.spatial.distance import cdist

def assign_to_clusters(pos_nodos, pos_CH):
    """
    Asignación de nodos a Cluster Heads (CH) basada en la distancia mínima.
    
    Parámetros:
    pos_nodos: array con las posiciones de los nodos (cada fila es [x, y] o [x, y, z]).
    pos_CH: array con las posiciones de los Cluster Heads (cada fila es [x, y] o [x, y, z]).
    
    Retorna:
    idx_CH: array con los índices del CH más cercano para cada nodo.
    """
    
    # Verificar si la lista de CH está vacía
    if len(pos_CH) == 0:
        return np.array([])
    
    # Calcular la distancia entre cada nodo y los Cluster Heads
    dist_CH = cdist(pos_nodos, pos_CH)  # Usa cdist para calcular la distancia entre dos conjuntos de puntos

    # Encontrar el índice del Cluster Head más cercano para cada nodo
    idx_CH = np.argmin(dist_CH, axis=1)

    return idx_CH

# # Ejemplo de uso en Python:
# pos_nodos = np.array([[0, 0], [1, 2], [2, 3], [4, 5]])
# pos_CH = np.array([[0, 1], [3, 4]])
# idx_CH = assign_to_clusters(pos_nodos, pos_CH)
# print(idx_CH)


# def update_energy(energia_nodos, pos_nodos, CH, idx_CH, sink_pos, a, EDA, E_schedule, P_r, freq, rounds_chacha, cifra):
def update_energy(energia_nodos, pos_nodos, CH, idx_CH, sink_pos, a, EDA, E_schedule, P_r, freq):
    """
    Cálculo de energía consumida durante la transmisión y recepción en una red de sensores submarina.
    
    Parámetros:
    energia_nodos: array con la energía actual de cada nodo.
    pos_nodos: matriz con las posiciones de los nodos (cada fila es [x, y] o [x, y, z]).
    CH: array con los índices de los Cluster Heads.
    idx_CH: array que asigna un CH a cada nodo.
    sink_pos: posición del Sink.
    a: factor de recepción (energía por bit recibido).
    EDA: energía de agregación de datos.
    E_schedule: energía consumida en la programación TDMA.
    P_r: potencia de recepción.
    freq: frecuencia de transmisión acústica (para el cálculo de la pérdida).
    rounds_chacha: número de rondas del cifrado ChaCha20.
    cifra: bandera para habilitar o deshabilitar el cifrado (1 = habilitar, 0 = deshabilitar).
    
    Retorna:
    energia_nodos: array actualizado con la energía restante de cada nodo.
    """
    num_nodos = len(energia_nodos)
    alpha = 1e-6  # Factor de energía por distancia (ajustable)
    L = 10 * 8  # Tamaño del paquete SYNC de 10 bytes, en bits

    for i in range(num_nodos):
        if i in CH:  # Si el nodo es un Cluster Head
            dCH2S = np.linalg.norm(pos_nodos[i] - sink_pos)  # Distancia al Sink
            loss_to_sink = acoustic_loss(dCH2S, freq)  # Pérdida acústica entre CH y Sink
            Et = L * (EDA + alpha * 10**(loss_to_sink/10) + E_schedule)  # Energía de transmisión ajustada por pérdida
            Er = P_r * a  # Energía de recepción

            # # Cálculo del consumo de energía por cifrado
            # if cifra == 1:
            #     tamano_mensaje = 10  # Tamaño del mensaje SYNC en bytes
            #     energia_cifrado = calcular_consumo_cifrado(rounds_chacha, tamano_mensaje)
            # else:
            #     energia_cifrado = 0

            energia_nodos[i] -= Et + Er #+ energia_cifrado  # Actualización de la energía

        else:  # Si el nodo no es CH
            dCM2CH = np.linalg.norm(pos_nodos[i] - pos_nodos[CH[idx_CH[i]]])  # Distancia al CH
            loss_to_CH = acoustic_loss(dCM2CH, freq)  # Pérdida acústica entre nodo normal y CH
            Et = L * (EDA + alpha * 10**(loss_to_CH/10))  # Energía de transmisión ajustada por pérdida
            Er = P_r * a  # Energía de recepción

            # # Cálculo del consumo de energía por cifrado
            # if cifra == 1:
            #     tamano_mensaje = 10  # Tamaño del mensaje SYNC en bytes
            #     energia_cifrado = calcular_consumo_cifrado(rounds_chacha, tamano_mensaje)
            # else:
            #     energia_cifrado = 0

            energia_nodos[i] -= Et + Er #+ energia_cifrado  # Actualización de la energía

        # Evitar que la energía se vuelva negativa
        if energia_nodos[i] < 0:
            energia_nodos[i] = 0

    return energia_nodos

# Funciones auxiliares necesarias para la conversión (como acoustic_loss y calcular_consumo_cifrado) deben definirse por separado.

import numpy as np
from test_throp import thorp_absorption

# def acoustic_loss(dist, freq):
#     """
#     Modelo de pérdida acústica basado en la distancia y la frecuencia, 
#     basado en el modelo de atenuación de Thorp y la teoría de propagación acústica de Urick.
    
#     Parámetros:
#     dist: distancia entre nodos (en metros).
#     freq: frecuencia de transmisión (en kHz).
    
#     Retorna:
#     L: pérdida acústica en dB.
#     """
    
#     # Parámetros típicos del medio acuático
#     alpha = 0.01  # Factor de absorción (dB/m) para la frecuencia dada (ajustar según el ambiente)
#     spreading_factor = 1.5  # Factor de propagación (generalmente entre 1 y 2)

#     # Cálculo de pérdida de transmisión (en dB)
#     # Pérdida por absorción: L_absorption = alpha * freq * dist
#     absorption_loss = alpha * freq * dist

#     # Pérdida por propagación (espacio libre o esférico): L_propagation = spreading_factor * log10(dist)
#     propagation_loss = spreading_factor * np.log10(dist)

#     # Pérdida total de señal (suma de absorción y propagación)
#     L = propagation_loss + absorption_loss  # Total en dB

#     return L

# Definir la función de pérdida acústica
def acoustic_loss(dist, freq):
    """
    Modelo de pérdida acústica basado en la distancia y la frecuencia, 
    basado en el modelo de atenuación de Thorp y la teoría de propagación acústica de Urick.
    
    Parámetros:
    dist: distancia entre nodos (en metros).
    freq: frecuencia de transmisión (en kHz).
    
    Retorna:
    L: pérdida acústica en dB.
    """
    
    if dist <= 0 or freq <= 0:
        raise ValueError("La distancia y la frecuencia deben ser mayores que cero.")

    # Parámetros típicos del medio acuático
    alpha = thorp_absorption(freq) / 1000  # Convertir a dB/m (ya que Thorp da dB/km)
    spreading_factor = 1.5  # Factor de propagación (generalmente entre 1 y 2)

    # Pérdida por absorción: L_absorption = alpha * dist
    absorption_loss = alpha * dist

    # Pérdida por propagación (espacio libre o esférico): L_propagation = spreading_factor * log10(dist)
    propagation_loss = spreading_factor * np.log10(dist)

    # Pérdida total de señal (suma de absorción y propagación)
    L = propagation_loss + absorption_loss  # Total en dB

    return L


# Ejemplo de uso en Python:
# dist = 1000  # Distancia entre nodos en metros
# freq = 10  # Frecuencia de transmisión en kHz
# L = acoustic_loss(dist, freq)
# print(f"Pérdida acústica: {L} dB")



#####

