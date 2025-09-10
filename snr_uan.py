# # “La relación señal/ruido (SNR) se ha estimado considerando la potencia de transmisión acústica, 
# # la pérdida de propagación en el canal subacuático (modelo de Thorp + dispersión geométrica), 
# # y el ruido ambiental según el modelo de Urick (1983). Esta métrica permite evaluar la viabilidad 
# # de la comunicación en función de la frecuencia, distancia, condiciones meteorológicas y actividad marítima.”

import numpy as np
from path_loss import compute_path_loss, propagation_time1
from noise_uan_aariza import compute_uan_noise

def transmission_power_db():
    """
    Potencia de transmisión en dB re 1 µPa²/Hz.
    Valores típicos: 160–190 dB para transmisores acústicos.
    """
    return 180.0  # ejemplo


def compute_snr(frequency_khz, distance_m, spread_coef=1.5, shipping=0.5, wind_speed=5.0):
    """
    Calcula la relación señal/ruido (SNR) en dB.
    """
    if isinstance(frequency_khz, str):
        frequency_khz = float(frequency_khz)
    if isinstance(distance_m, str):
        distance_m = float(distance_m)

    tx_power_db = transmission_power_db()
    path_loss_db, _ = compute_path_loss(frequency_khz, distance_m, spread_coef)
    noise_db, _ = compute_uan_noise(frequency_khz, shipping, wind_speed)

    rx_power_db = tx_power_db - path_loss_db
    snr_db = rx_power_db - noise_db

    return snr_db, {
        "tx_power_db": tx_power_db,
        "rx_power_db": rx_power_db,
        "path_loss_db": path_loss_db,
        "noise_db": noise_db
    }


def evaluate_link_quality(start_position, end_position, frequency_khz, spread_coef, shipping, wind_speed, region="standard"):
    distance_m = np.linalg.norm(np.array(end_position) - np.array(start_position))
    snr_db, snr_details = compute_snr(frequency_khz, distance_m, spread_coef, shipping, wind_speed)
    delay_s = propagation_time1(start_position, end_position, depth=None, region="standard")
    return {
        "snr_db": snr_db,
        "delay_s": delay_s,
        "details": snr_details
    }

# # Para simular varios enlaces
def simulate_links(start, ends, freq, spread_coef, shipping, wind_speed, region):
    results = []
    for end in ends:
        result = evaluate_link_quality(start, end, freq, spread_coef, shipping, wind_speed, region)
        results.append({
            "end_position": end,
            "snr_db": result["snr_db"],
            "delay_s": result["delay_s"]
        })
    return results


freq = 20  # kHz
shipping = 0.5
wind_speed = 5.0
spread_coef = 1.5

start_position = (1000, 1000, 0)  # Coordenadas (x, y, z) del transmisor
end_position = (1000, 1000, 1000.71)  # Coordenadas (x, y, z) del receptor

distance = np.linalg.norm(np.array(end_position) - np.array(start_position)) # Distancia en metros

snr, details = compute_snr(freq, distance, spread_coef=1.5, shipping=shipping, wind_speed=wind_speed)
print(f"SNR a {freq} kHz y {distance} m: {snr:.2f} dB")
for k, v in details.items():
    print(f"  {k:<15}: {v:.2f} dB")

# Evaluar calidad del enlace

snr_details = evaluate_link_quality(start_position, end_position, freq, spread_coef, shipping, wind_speed)

# Mostrar resultados
print(f"\n📡 Evaluación del enlace acústico:")
print(f"  Frecuencia: {freq} kHz")
print(f"  Distancia: {distance:.2f} m")
print(f"  SNR: {snr_details['snr_db']:.2f} dB re 1 µPa²/Hz")
print(f"  Retardo: {snr_details['delay_s']:.4f} s")
print("  Detalles:")
for key, value in snr_details["details"].items():
    print(f"    {key:<15}: {value:.2f} dB")

