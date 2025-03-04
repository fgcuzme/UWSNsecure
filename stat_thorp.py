import matplotlib.pyplot as plt
import numpy as np

# Activar modo interactivo
#plt.ion()

# Fórmula de Thorp
def thorp(f):
    return (0.11 * f**2) / (1 + f**2) + (44 * f**2) / (4100 + f**2) + 0.00275 * f**2 + 0.003

frecuencias = np.linspace(1, 100, 100)
perdida = thorp(frecuencias)

plt.plot(frecuencias, perdida)
plt.xlabel("Frecuencia (kHz)")
plt.ylabel("Pérdida por absorción (dB/km)")
plt.title("Modelo de Thorp en UAN")
plt.show()
#plt.show(block=False)
