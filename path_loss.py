import numpy as np
from temperature_models import get_temperature # type: ignore

# Constantes para tipos de dispersión
SPHERICAL = 2
CYLINDRICAL = 1
MIXED = 1.5

# # Donde α tiene unidades de dB·km-1 y f es la frecuencia de la señal en kHz. El último
# # término es una corrección que tiene en cuenta la absorción a muy baja frecuencia,
# # siendo esta ecuación válida para temperaturas de 4ºC y una profundidad de 900 m,
# # que es donde se tomaron las medidas [2]. 

def thorp_absorptionDbKm(frequency_khz):
    """Calcula la absorción acústica en dB/km según la fórmula de Thorp."""
    if frequency_khz <= 0:
        raise ValueError("La frecuencia debe ser positiva.")

    fsq = frequency_khz * frequency_khz
    # Fórmula de Thorp para calcular absorción en dB/km
    if (frequency_khz >= 0.4):
        # alpha = (0.11 * frequency_khz**2) / (1 + frequency_khz**2) + (44 * frequency_khz**2) / (4100 + frequency_khz) + 2.75e-4 * frequency_khz**2 + 0.003
        # alpha = (0.11 * frequency_khz**2) / (1 + frequency_khz**2) + (44 * frequency_khz**2) / (4100 + frequency_khz) + (2.75 * 10**-4) * frequency_khz**2 + 0.003
        alpha = (0.11 * fsq / (1 + fsq) + 44 * fsq / (4100 + fsq) + 2.75e-4 * fsq + 0.003)
    else:
        alpha = 0.002 + 0.11 * (frequency_khz / (1 + frequency_khz)) + 0.011 * frequency_khz
    return alpha # dB/Km

# # Ejemplo de uso:
# frecuencia = 20  # Frecuencia en kHz

# absorcion = thorp_absorptionDbKm(frecuencia)

# print(f"Absorción acústica a {frecuencia} kHz: {absorcion:.2f} dB/km")

# # Spreading Factor
# # El spreading factor es otra contribución a la pérdida de señal y depende de la geometría de propagación. Existen dos tipos principales:
# # Esférico (spreading = 2): Se asume en propagación en campo abierto (una señal se expande en todas las direcciones).
# # Cilíndrico (spreading = 1): Para ambientes donde la señal se propaga en capas, como en canales subacuáticos.
# # Análisis
# # Para obtener el total de pérdidas en dB:

# # 𝐿 = 20 log b10 (𝑑) + 𝛼 ⋅ 𝑑
# # L = 10 log b10 (𝑑) + 𝛼 ⋅ 𝑑

# # donde:
# # 𝐿 = es la pérdida total (dB),
# # 𝑑 = es la distancia (en km),
# # 𝛼 = es la pérdida de absorción por kilómetro (dB/km).
# # El spreading factor ( 20 log 10 ( 𝑑 ) representa las pérdidas geométricas, y la absorción acústica 𝛼 se suma para calcular las pérdidas totales.

# ##
# # El spreading factor proviene de las características de propagación de ondas en el medio subacuático y se utiliza en la ecuación de transmisión acústica para modelar las pérdidas geométricas. Se basa en el tipo de expansión de la onda:
# # Esférico (3D spreading): Ocurre cuando la señal se propaga en todas las direcciones, como en un entorno sin barreras. La pérdida es proporcional a 
# # 20 log b10 (10)
# # Cilíndrico (2D spreading): Se da en entornos como canales acústicos, donde la propagación es limitada horizontalmente, con pérdidas de 
# # 10 log b10 (d)

# # spherical -> 2
# # cylindrical -> 1
# # mixed -> 1.5

def spreading_loss(distance_m, spreading_type):
    """Calcula la pérdida por dispersión geométrica en dB."""
    if distance_m <= 0:
        raise ValueError("La distancia debe ser positiva.")

    """
    Calcula la pérdida por dispersión (spreading loss) para una señal acústica.
    Parameters:
    - distance (float): La distancia de propagación en metros.
    - spreading_type (str): Tipo de dispersión ('spherical' para esférico o 'cylindrical' para cilíndrico).
    Returns:
    - float: Pérdida en dB.
    """
    if spreading_type == 2:
        return 20 * np.log10(distance_m)  # Pérdida esférica
    elif spreading_type == 1:
        return 10 * np.log10(distance_m)  # Pérdida cilíndrica
    elif spreading_type == 1.5:
        return 15 * np.log10(distance_m)  # Pérdida mixta
    else:
        raise ValueError("Tipo de dispersión no válido. Use 'spherical', 'cylindrical' o 'M¿mixed'.")



def compute_path_loss(frequency_khz: float, distance_m: float, spread_coef: float = 1.5):
        """Calcula la pérdida total en dB y su equivalente lineal."""
        """
        Calcula la pérdida de propagación en el canal acústico submarino.
        :param frequency_khz: Frecuencia en kHz
        :param distance_m: Distancia en metros
        :param spread_coef: Coeficiente de dispersión (1, 1.5, 2)
        :return: Pérdida en dB y fracción lineal
        """
        # attenuation_db = (self.spread_coef * 10.0 * math.log10(distance) +
        #                   (distance / 1000.0) * self.get_atten_db_km(frequency / 1000.0))

        distance_km = distance_m / 1000.0  # Normalización explícita
        alpha_db_per_km = thorp_absorptionDbKm(frequency_khz)  # dB/km
        spreading_db = spreading_loss(distance_m, spread_coef)  # dB

        attenuation_db = spreading_db + alpha_db_per_km * distance_km
        attenuation_linear = 10 ** (-attenuation_db / 10)

        #attenuation_db = spreading_loss(distance, spread_coef) +  (distance/1000.0) * thorp_absorptionDbKm(frequency_khz)

        # print(" attenuation_db : ", attenuation_db)
        # print(" attenuation_lineal : ", attenuation_linear)

        return attenuation_db, attenuation_linear


def compute_range(frequency_khz: float, loss_linear: float):
    """Calcula la distancia máxima alcanzable en metros para una pérdida dada."""
    """
    Calcula el alcance máximo basado en la frecuencia y la pérdida de señal.
    :param propagation_speed: Velocidad de propagación del sonido en el agua (m/s)
    :param frequency: Frecuencia en KHz
    :param loss: Factor de pérdida permitido
    :return: Distancia máxima en metros
    """
    if loss_linear <= 0:
        raise ValueError("La pérdida debe ser positiva.")
    
    alpha_db_per_km = thorp_absorptionDbKm(frequency_khz)
    alpha_linear = 10 ** (-alpha_db_per_km / 10)
    distance_km = loss_linear / alpha_linear

    # att = 10 ** (-thorp_absorptionDbKm(frequency_khz) / 10)  # Conversión de dB a fracción
    # distance = 1000 * loss / att
    return distance_km * 1000 # metros


def compute_range_real(frequency_khz: float, loss_linear: float, spread_coef: float = 1.5):
    """
    Calcula la distancia máxima alcanzable en metros para una pérdida total dada.
    """
    if loss_linear <= 0:
        raise ValueError("La pérdida debe ser positiva.")

    # Convertir pérdida lineal a dB
    total_loss_db = -10 * np.log10(loss_linear)

    # Absorción acústica
    alpha_db_per_km = thorp_absorptionDbKm(frequency_khz)

    # Resolver la ecuación: L = spreading + alpha * d
    # L = spread_coef * 10 * log10(d) + alpha * d
    # Usamos método numérico para encontrar d

    def loss_equation(d_km):
        return spread_coef * 10 * np.log10(d_km * 1000) + alpha_db_per_km * d_km - total_loss_db

    from scipy.optimize import brentq
    try:
        d_km = brentq(loss_equation, 0.001, 100)  # buscar entre 1 m y 100 km
        return d_km * 1000  # metros
    except ValueError:
        return None  # no se puede alcanzar con esa pérdida



#def random_speed_of_sound(depth = random.uniform(0, 1000)): # Se cambia por la linea siguiente
def random_speed_of_sound(depth, region="standard", salinity=None):
    """Calcula la velocidad del sonido usando la fórmula de Mackenzie (1981)."""
    # Rango de temperatura en °C
    # temp = np.random.uniform(0, 30) #°C
    # envio la depth completa para la elección de la temperatura
    depth_total = depth * 2
    # temp = temperature_profile(depth_total)
    temp = get_temperature(depth_total, region)
    # Rango de salinidad en ppt
    salinity = salinity if salinity is not None else np.random.uniform(30, 40)   # ppt

    # Ecuación de Mackenzie para calcular la velocidad del sonido en el agua
    v = (1448.96 + 4.591 * temp - 5.304e-2 * temp**2 + 2.374e-4 * temp**3 + 
         1.340 * (salinity - 35) + 1.630e-2 * depth + 1.675e-7 * depth**2 - 
         1.025e-2 * temp * (salinity - 35) - 7.139e-13 * temp * depth**3)
    
    return v, temp, salinity, depth_total # m/s, °C, ppt, m

# Ejemplo de uso:
# velocidad, temp, sal, prof = random_speed_of_sound(100)
# print(f"Velocidad del sonido: {velocidad:.2f} m/s a {temp:.2f}°C, {sal:.2f} ppt, {prof:.2f} m")

# # Para calcular el tiempo de propagación de una señal acústica en un entorno subacuático, se puede usar la fórmula
# # t = d / v
# #donde:
# # 𝑡 = es el tiempo de propagación (en segundos),
# # 𝑑 = es la distancia entre el emisor y el receptor (en metros),
# # 𝑣 = es la velocidad del sonido en el agua (en metros por segundo).
# # La velocidad del sonido en el agua puede variar dependiendo de la temperatura, la salinidad y la presión.

def propagation_time(dist, start_position, end_position):
    """Calcula el tiempo de propagación acústica entre dos puntos."""
    """
    Calcula el tiempo de propagación de una señal acústica.
    Parámetros:
    - dist: Distancia en metros entre el emisor y el receptor.
    - speed: Velocidad del sonido en el agua (por defecto 1500 m/s).
    Retorna:
    - Tiempo de propagación en segundos.
    """
    # Calcular la profundidad media, calculada en metros
    depth = np.abs((start_position[2] - end_position[2]) / 2 + end_position[2])
    
    # print("Profundidad en metros : ", depth)

    # Se calcula la velocidad del sonido de acuerdo a la formula de Mackenzie
    speed, temp, sal, prof = random_speed_of_sound(depth)

    # print(f"Velocidad calculada con la formula de Mackenzie: {speed:.2f} m/s a {temp:.2f}°C, {sal:.2f} ppt, {prof:.2f} m")

    return dist / speed


def propagation_time1(start_position, end_position, depth=None, region="standard"):
    """Calcula el tiempo de propagación acústica entre dos puntos."""
    """
    Calcula el tiempo de propagación de una señal acústica.
    Parámetros:
    - dist: Distancia en metros entre el emisor y el receptor.
    - speed: Velocidad del sonido en el agua (por defecto 1500 m/s).
    Retorna:
    - Tiempo de propagación en segundos.
    """
    distance_m = np.linalg.norm(np.array(end_position) - np.array(start_position))

    # print("Distancia calculada : ", distance_m)

    # Calcular la profundidad media, calculada en metros
    if depth is None:
        depth = np.abs((start_position[2] - end_position[2]) / 2 + end_position[2])
    
    # print("Profundidad en metros : ", depth)

    # Se calcula la velocidad del sonido de acuerdo a la formula de Mackenzie
    speed, temp, sal, prof = random_speed_of_sound(depth, region)

    # print(f"Velocidad calculada con la formula de Mackenzie: {speed:.2f} m/s a {temp:.2f}°C, {sal:.2f} ppt, {prof:.2f} m")

    return distance_m / speed


# Ejemplo de uso:

frequency_khz = 20 
start_position = (1000, 1000, 0)  # Coordenadas (x, y, z) del transmisor
end_position = (1000, 1000, 1000.71)  # Coordenadas (x, y, z) del receptor
distance_m = np.linalg.norm(np.array(end_position) - np.array(start_position)) # Distancia en metros
print("Distancia calculada : ", distance_m)

depth = np.abs((start_position[2] - end_position[2]) / 2 + end_position[2])
velocidad, temp, sal, prof = random_speed_of_sound(depth)
print(f"Velocidad del sonido: {velocidad:.2f} m/s a {temp:.2f}°C, {sal:.2f} ppt, {prof:.2f} m")

tiempo = propagation_time(distance_m, start_position, end_position)
print(f"El tiempo de propagación es {tiempo:.2f} segundos")

tiempo1 = propagation_time1(start_position, end_position, depth=None, region="standard")
print(f"El tiempo de propagación calculo nuevo {tiempo1:.2f} segundos")

print(f"Pérdida esférica: {spreading_loss(distance_m, SPHERICAL)} dB")
print(f"Pérdida cilíndrica: {spreading_loss(distance_m, CYLINDRICAL)} dB")
print(f"Pérdida mixta: {spreading_loss(distance_m, MIXED)} dB")


print(f"Perdida total path_loss (spherical) : ", compute_path_loss(frequency_khz, distance_m, SPHERICAL))
print(f"Perdida total path_loss (cylindrical) : ", compute_path_loss(frequency_khz, distance_m, CYLINDRICAL))
print(f"Perdida total path_loss (mixta) : ", compute_path_loss(frequency_khz, distance_m, MIXED))

# Ejemplo de cálculo del rango máximo
loss_linear = 1e-2  # Factor de pérdida permitido
print(f"Distancia máxima alcanzable: {compute_range(frequency_khz, loss_linear)} metros")
print(f"Distancia máxima alcanzable real: {compute_range_real(frequency_khz, loss_linear, spread_coef = 1.5)} metros")