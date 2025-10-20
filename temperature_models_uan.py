import numpy as np

def get_temperature(depth, region="standard"):
    if region == "standard":
        return temperature_profile(depth)
    elif region == "tropical":
        return temperature_profile_tc(depth)
    else:
        raise ValueError("Región no válida. Use 'standard' o 'tropical'.")


# # “Se ha implementado un perfil térmico vertical simplificado para representar la variación de temperatura con la profundidad.
# # Este modelo está basado en observaciones oceanográficas descritas por Talley et al. (2011) "Chapter 4 - Typical Distributions of Water Characteristics" y 
# # refleja la estructura típica de capas térmicas en ambientes marinos. 
# # Su incorporación permite mejorar la estimación de la velocidad del sonido en función de la profundidad.”

# # La función propuesta genera temperaturas en los siguientes rangos:
# # - Capa superficial (0–100 m): de 25 °C a 15 °C
# # - Termoclina (100–500 m): de 15 °C a 7 °C
# # - Capa profunda (>500 m): constante en 7 °C

# # “El perfil térmico vertical implementado genera temperaturas entre 7 °C y 25 °C, lo cual se encuentra dentro 
# # del rango de validez de la ecuación de Mackenzie (0–30 °C). Por tanto, la estimación de la velocidad del sonido
# # basada en este perfil es científicamente coherente y adecuada para entornos oceánicos típicos.”

def temperature_profile(depth):
    """
    Modelo simplificado de perfil térmico oceánico basado en Talley et al. (2011).
    - Capa superficial (0–100 m): disminución rápida por radiación solar.
    - Termoclina (100–500 m): gradiente térmico moderado.
    - Capa profunda (>500 m): temperatura estable (~7 °C).
    """

    if depth < 100:
        return 25 - 0.1 * depth
    elif depth < 500:
        return 15 - 0.02 * (depth - 100)
    else:
        return 7
    

# # “El perfil térmico ha sido ajustado para representar condiciones tropicales costeras, 
# # donde la temperatura superficial puede alcanzar hasta 30 °C. Este ajuste sigue siendo 
# # compatible con la ecuación de Mackenzie, cuyo rango de validez incluye temperaturas entre 0 °C y 30 °C.”

def temperature_profile_tc(depth):
    """
    Perfil térmico ajustado para aguas tropicales cálidas.
    """
    if depth < 50:
        return 30 - 0.1 * depth  # hasta 25 °C a 50 m
    elif depth < 300:
        return 25 - 0.02 * (depth - 50)
    else:
        return 10
