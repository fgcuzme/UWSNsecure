import random
import math
import numpy as np

def random_speed_of_sound():
    # Rango de temperatura en °C
    temp = random.uniform(0, 30)
    # Rango de salinidad en ppt
    salinity = random.uniform(30, 40)
    # Rango de profundidad en metros
    depth = random.uniform(0, 1000)
    # depth = 100
    
    # Ecuación de Mackenzie para calcular la velocidad del sonido en el agua
    v = (1448.96 + 4.591 * temp - 5.304e-2 * temp**2 + 2.374e-4 * temp**3 + 
         1.340 * (salinity - 35) + 1.630e-2 * depth + 1.675e-7 * depth**2 - 
         1.025e-2 * temp * (salinity - 35) - 7.139e-13 * temp * depth**3)
    
    return v, temp, salinity, depth

# Ejemplo de uso:
velocidad, temp, sal, prof = random_speed_of_sound()
print(f"Velocidad del sonido: {velocidad:.2f} m/s a {temp:.2f}°C, {sal:.2f} ppt, {prof:.2f} m")


# Para calcular el tiempo de propagación de una señal acústica en un entorno subacuático, se puede usar la fórmula
# t = d / v
#donde:
# 𝑡 = es el tiempo de propagación (en segundos),
# 𝑑 = es la distancia entre el emisor y el receptor (en metros),
# 𝑣 = es la velocidad del sonido en el agua (en metros por segundo).
# La velocidad del sonido en el agua puede variar dependiendo de la temperatura, la salinidad y la presión.

def propagation_time(dist, speed=1500):
    """
    Calcula el tiempo de propagación de una señal acústica.
    
    Parámetros:
    - dist: Distancia en metros entre el emisor y el receptor.
    - speed: Velocidad del sonido en el agua (por defecto 1500 m/s).
    
    Retorna:
    - Tiempo de propagación en segundos.
    """
    if dist <= 0:
        return 0  # Evitar valores negativos o nulos de distancia
    
    # Se calcula la velocidad del sonido de acuerdo a la formula de Mackenzie
    speed, temp, sal, prof = random_speed_of_sound()
    # print(f"Velocidad calculada con la formula de Mackenzie: {velocidad:.2f} m/s a {temp:.2f}°C, {sal:.2f} ppt, {prof:.2f} m")

    return dist / speed

distancia = 500  # Distancia en metros
tiempo = propagation_time(distancia)
print(f"El tiempo de propagación es {tiempo:.2f} segundos")


# Donde α tiene unidades de dB·km-1 y f es la frecuencia de la señal en kHz. El último
# término es una corrección que tiene en cuenta la absorción a muy baja frecuencia,
# siendo esta ecuación válida para temperaturas de 4ºC y una profundidad de 900 m,
# que es donde se tomaron las medidas [2]. 

def thorp_absorption(frequency_khz):
    fsq = frequency_khz * frequency_khz
    # Fórmula de Thorp para calcular absorción en dB/km
    if (frequency_khz >= 0.4):
        # alpha = (0.11 * frequency_khz**2) / (1 + frequency_khz**2) + (44 * frequency_khz**2) / (4100 + frequency_khz) + 2.75e-4 * frequency_khz**2 + 0.003
        # alpha = (0.11 * frequency_khz**2) / (1 + frequency_khz**2) + (44 * frequency_khz**2) / (4100 + frequency_khz) + (2.75 * 10**-4) * frequency_khz**2 + 0.003
        alpha = (0.11 * fsq / (1 + fsq) + 44 * fsq / (4100 + fsq) + 2.75e-4 * fsq + 0.003)
    else:
        alpha = 0.002 + 0.11 * (frequency_khz / (1 + frequency_khz)) + 0.011 * frequency_khz
    return alpha

# Ejemplo de uso:
frecuencia = 20  # Frecuencia en kHz

absorcion = thorp_absorption(frecuencia)

print(f"Absorción acústica a {frecuencia} kHz: {absorcion:.2f} dB/km")

# Spreading Factor
# El spreading factor es otra contribución a la pérdida de señal y depende de la geometría de propagación. Existen dos tipos principales:
# Esférico (spreading = 2): Se asume en propagación en campo abierto (una señal se expande en todas las direcciones).
# Cilíndrico (spreading = 1): Para ambientes donde la señal se propaga en capas, como en canales subacuáticos.
# Análisis
# Para obtener el total de pérdidas en dB:

# 𝐿 = 20 log b10 (𝑑) + 𝛼 ⋅ 𝑑
# L = 10 log b10 (𝑑) + 𝛼 ⋅ 𝑑

# donde:
# 𝐿 = es la pérdida total (dB),
# 𝑑 = es la distancia (en km),
# 𝛼 = es la pérdida de absorción por kilómetro (dB/km).
# El spreading factor ( 20 log 10 ( 𝑑 ) representa las pérdidas geométricas, y la absorción acústica 𝛼 se suma para calcular las pérdidas totales.

##
# El spreading factor proviene de las características de propagación de ondas en el medio subacuático y se utiliza en la ecuación de transmisión acústica para modelar las pérdidas geométricas. Se basa en el tipo de expansión de la onda:
# Esférico (3D spreading): Ocurre cuando la señal se propaga en todas las direcciones, como en un entorno sin barreras. La pérdida es proporcional a 
# 20 log b10 (10)
# Cilíndrico (2D spreading): Se da en entornos como canales acústicos, donde la propagación es limitada horizontalmente, con pérdidas de 
# 10 log b10 (d)

# spherical -> 2
# cylindrical -> 1
# mixed -> 1.5

import numpy as np

def spreading_loss(distance, spreading_type):
    """
    Calcula la pérdida por dispersión (spreading loss) para una señal acústica.

    Parameters:
    - distance (float): La distancia de propagación en metros.
    - spreading_type (str): Tipo de dispersión ('spherical' para esférico o 'cylindrical' para cilíndrico).
    
    Returns:
    - float: Pérdida en dB.
    """
    if spreading_type == 2:
        return 20 * np.log10(distance)  # Pérdida esférica
    elif spreading_type == 1:
        return 10 * np.log10(distance)  # Pérdida cilíndrica
    elif spreading_type == 1.5:
        return 15 * np.log10(distance)  # Pérdida mixta
    else:
        raise ValueError("Tipo de dispersión no válido. Use 'spherical' o 'cylindrical'.")


def compute_path_loss(frequency_khz: float, distance: float, spread_coef: float = 1.5):
        """
        Calcula la pérdida de propagación en el canal acústico submarino.
        :param propagation_speed: Velocidad de propagación del sonido en el agua (m/s)
        :param frequency: Frecuencia en Hz
        :param distance: Distancia en metros
        :return: Pérdida de propagación en factor de fracción (no en dB)
        # """
        # attenuation_db = (self.spread_coef * 10.0 * math.log10(distance) +
        #                   (distance / 1000.0) * self.get_atten_db_km(frequency / 1000.0))
        
        attenuation_db = spreading_loss(distance, spread_coef) +  (distance/1000.0) * thorp_absorption(frequency_khz)

        # print(" attenuation_db : ", attenuation_db)

        return attenuation_db, 10 ** (-attenuation_db / 10)  # Conversión de dB a fracción


def compute_range(frequency: float, loss: float):
    """
    Calcula el alcance máximo basado en la frecuencia y la pérdida de señal.
    :param propagation_speed: Velocidad de propagación del sonido en el agua (m/s)
    :param frequency: Frecuencia en Hz
    :param loss: Factor de pérdida permitido
    :return: Distancia máxima en metros
    """
    att = 10 ** (-thorp_absorption(frequency) / 10)  # Conversión de dB a fracción
    distance = 1000 * loss / att
    return distance


# Ejemplo de uso:
# distancia = 1500  # metros
print(f"Pérdida esférica: {spreading_loss(distancia, 2)} dB")
print(f"Pérdida cilíndrica: {spreading_loss(distancia, 1)} dB")
print(f"Pérdida mixta: {spreading_loss(distancia, 1.5)} dB")


print(f"Perdida total path_loss (spherical) : ", compute_path_loss(frecuencia, distancia, 2))
print(f"Perdida total path_loss (cylindrical) : ", compute_path_loss(frecuencia, distancia, 1))
print(f"Perdida total path_loss (mixta) : ", compute_path_loss(frecuencia, distancia, 1.5))

# Ejemplo de cálculo del rango máximo
loss = 1e-3  # Factor de pérdida permitido
print(f"Distancia máxima alcanzable: {compute_range(frecuencia, loss)} metros")