# # “El modelo de ruido ambiental implementado se basa en las ecuaciones empíricas descritas por Urick (1983), 
# # que descomponen el ruido subacuático en componentes de turbulencia, tráfico marítimo, viento y ruido térmico. 
# # Este enfoque permite estimar el nivel de ruido en función de la frecuencia, 
# # condiciones meteorológicas y actividad humana, siendo ampliamente utilizado en simulaciones acústicas submarinas.”

import numpy as np

def compute_uan_noise(frequency_khz, shipping, wind_speed_mps):
    """
    Calcula el ruido ambiental en dB re 1 µPa^2/Hz según Urick (1983).
    
    Parámetros:
    - frequency_khz: Frecuencia en kHz
    - shipping: Nivel de tráfico marítimo (0 a 1)
    - wind_speed: Velocidad del viento en m/s
    
    Retorna:
    - Ruido total en dB
    - Componentes individuales en dB
    """
    if frequency_khz <= 0:
        raise ValueError("La frecuencia debe ser positiva.")

    fKhz = frequency_khz

    # Componentes en dB
    turb_db = 17.0 - 30.0 * np.log10(fKhz)
    ship_db = 40.0 + 20.0 * (shipping - 0.5) + 26.0 * np.log10(fKhz) - 60.0 * np.log10(fKhz + 0.03)
    wind_db = 50.0 + 7.5 * np.sqrt(wind_speed_mps) + 20.0 * np.log10(fKhz) - 40.0 * np.log10(fKhz + 0.4)
    thermal_db = -15.0 + 20.0 * np.log10(fKhz)

    # Conversión a escala lineal
    turb = 10 ** (turb_db / 10)
    ship = 10 ** (ship_db / 10)
    wind = 10 ** (wind_db / 10)
    thermal = 10 ** (thermal_db / 10)

    # Suma total en escala lineal
    total_noise_linear = turb + ship + wind + thermal
    total_noise_db = 10 * np.log10(total_noise_linear)

    return total_noise_db, {
        "turbulence_dB": turb_db,
        "shipping_dB": ship_db,
        "wind_dB": wind_db,
        "thermal_dB": thermal_db,
    }


freq = 20  # kHz
shipping = 0.5
wind_speed = 5.0

total_db, components = compute_uan_noise(freq, shipping, wind_speed)
print(f"Ruido total a {freq} kHz: {total_db:.2f} dB re 1 µPa^2/Hz")
for k, v in components.items():
    print(f"  {k.capitalize():<10}: {v:.2f} dB")
