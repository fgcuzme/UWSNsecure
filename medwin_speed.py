# Reejecutar el código después del reinicio

import numpy as np

class UnderwaterPropagation:
    def __init__(self, temperature=10, salinity=35, depth=100, use_mean_depth=False):
        """
        Inicializa los parámetros del modelo de propagación submarina.
        :param temperature: Temperatura del agua en °C
        :param salinity: Salinidad en partes por mil (PPT)
        :param depth: Profundidad promedio en metros
        :param use_mean_depth: Si se usa la profundidad media para el cálculo
        """
        self.temperature = temperature
        self.salinity = salinity
        self.depth = depth
        self.use_mean_depth = use_mean_depth

    def compute_speed_of_sound(self, depth=None):
        """
        Calcula la velocidad del sonido en el agua en función de la temperatura, salinidad y profundidad.
        :param depth: Profundidad en metros (opcional)
        :return: Velocidad del sonido en m/s
        """
        if depth is None:
            depth = self.depth

        # Ecuación empírica para la velocidad del sonido en el agua
        speed = (1449.2 + 4.6 * self.temperature 
                 - 0.055 * self.temperature ** 2 + 0.00029 * self.temperature ** 3
                 + (1.34 - 0.01 * self.temperature) * (self.salinity - 35) 
                 + 0.16 * depth)
        return speed

    def compute_arrival_time(self, start_position, end_position, start_time):
        """
        Calcula el tiempo de llegada de una señal acústica submarina.
        :param start_position: Coordenada (x, y, z) inicial
        :param end_position: Coordenada (x, y, z) final
        :param start_time: Tiempo de inicio de la transmisión en segundos
        :return: Tiempo de llegada en segundos
        """
        start_position = np.array(start_position)
        end_position = np.array(end_position)

        # Calcular la profundidad media si está habilitada
        if self.use_mean_depth:
            depth = np.abs((start_position[2] - end_position[2]) / 2 + end_position[2])
        else:
            depth = self.depth

        # Obtener la velocidad del sonido en función de la profundidad
        speed_of_sound = self.compute_speed_of_sound(depth)
        print("Velocidad calculada con Medwin : ", speed_of_sound)

        # Calcular la distancia entre los puntos
        distance = np.linalg.norm(end_position - start_position)

        # Tiempo de propagación
        propagation_time = distance / speed_of_sound

        # Calcular el tiempo de llegada
        arrival_time = start_time + propagation_time

        return arrival_time

# Definir parámetros de prueba
temperature = 10  # Temperatura en °C
salinity = 35  # Salinidad en PPT
depth = 150  # Profundidad en metros
use_mean_depth = True

# Crear el modelo de propagación
propagation_model = UnderwaterPropagation(temperature, salinity, depth, use_mean_depth)

# Definir posiciones y tiempos
start_position = (10, 10, 0)  # Coordenadas (x, y, z) del transmisor
end_position = (1000, 100, -10)  # Coordenadas (x, y, z) del receptor
start_time = 0  # Tiempo de inicio en segundos

# Calcular el tiempo de llegada
arrival_time = propagation_model.compute_arrival_time(start_position, end_position, start_time)

# Mostrar resultados
arrival_time
print("Time of arrival : ", arrival_time)