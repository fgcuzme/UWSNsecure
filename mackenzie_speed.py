import numpy as np

def mackenzie_speed(temp, salinity, depth):
    v = 1448.96 + 4.591 * temp - 5.304e-2 * temp**2 + 2.374e-4 * temp**3
    v += 1.340 * (salinity - 35) + 1.630e-2 * depth + 1.675e-7 * depth**2
    v -= 1.025e-2 * temp * (salinity - 35) + 7.139e-13 * temp * depth**3
    return v  # m/s

def thorp_absorption(f_kHz):
    f_sq = f_kHz**2
    alpha_dB_km = (0.11 * f_sq)/(1 + f_sq) + (44 * f_sq)/(4100 + f_sq) + 2.75e-4 * f_sq + 0.003
    return alpha_dB_km  # dB/km

# Parámetros
temp = 10    # °C
salinity = 35 # ppt
depth = 100  # metros
f = 10       # kHz

# Calcular velocidad y atenuación
v = mackenzie_speed(temp, salinity, depth)
alpha_dB_km = thorp_absorption(f)
alpha_nepers_m = alpha_dB_km * 0.1151 / 1000  # Convertir a nepers/m

# Pérdida total a una distancia r (ejemplo para r = 1000 m)
r = 1000
presion_relativa = np.exp(-alpha_nepers_m * r) / r
print(f"Presión relativa a {r} m: {presion_relativa:.2e}")