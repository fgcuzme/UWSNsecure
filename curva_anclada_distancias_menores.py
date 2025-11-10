import numpy as np
from path_loss import compute_path_loss              # TL(d,f)
from noise_uan_aariza import compute_uan_noise       # NL_psd(f)
import matplotlib.pyplot as plt
import os

def bandwidth_bpsk_rrc(Rb_bps: float, alpha: float = 0.35) -> float:
    return Rb_bps * (1.0 + alpha)

def nl_total_db(f_khz: float, shipping: float, wind_mps: float, B_hz: float) -> float:
    nl_psd_db, _ = compute_uan_noise(f_khz, shipping, wind_mps)
    return float(nl_psd_db + 10.0*np.log10(B_hz))

def tl_db(f_khz: float, d_m: float, k_spread: float) -> float:
    tl, _ = compute_path_loss(f_khz, d_m, k_spread)
    return float(tl)

def p_tx_approx_W(d_m: float,
                  f_khz: float = 20.0,
                  Rb_bps: float = 9200.0,
                  alpha: float = 0.35,
                  k_spread: float = 1.5,
                  shipping: float = 0.5,
                  wind_mps: float = 5.0,
                  d_ref_m: float = 1500.0,
                  P_ref_W: float = 2.5) -> float:
    """
    Potencia 'aproximada' (cota inferior física) para d<1500 m,
    anclada a P_ref_W=2.5 W en d_ref_m=1500 m.
    """
    B_hz = bandwidth_bpsk_rrc(Rb_bps, alpha)
    TL = tl_db(f_khz, d_m, k_spread)
    TL_ref = tl_db(f_khz, d_ref_m, k_spread)
    NLt = nl_total_db(f_khz, shipping, wind_mps, B_hz)
    NLt_ref = nl_total_db(f_khz, shipping, wind_mps, B_hz)
    delta = (TL - TL_ref) + (NLt - NLt_ref)  # dB
    return float(P_ref_W * (10.0 ** (delta/10.0)))

def p_tx_approx_W3000(d_m: float,
                  f_khz: float = 20.0,
                  Rb_bps: float = 9200.0,
                  alpha: float = 0.35,
                  k_spread: float = 1.5,
                  shipping: float = 0.5,
                  wind_mps: float = 5.0,
                  d_ref_m: float = 3000.0,
                  P_ref_W: float = 5.0) -> float:
    """
    Potencia 'aproximada' (cota inferior física) para d<1500 m,
    anclada a P_ref_W=2.5 W en d_ref_m=1500 m.
    """
    B_hz = bandwidth_bpsk_rrc(Rb_bps, alpha)
    TL = tl_db(f_khz, d_m, k_spread)
    TL_ref = tl_db(f_khz, d_ref_m, k_spread)
    NLt = nl_total_db(f_khz, shipping, wind_mps, B_hz)
    NLt_ref = nl_total_db(f_khz, shipping, wind_mps, B_hz)
    delta = (TL - TL_ref) + (NLt - NLt_ref)  # dB
    return float(P_ref_W * (10.0 ** (delta/10.0)))

def p_tx_approx_W6000(d_m: float,
                  f_khz: float = 20.0,
                  Rb_bps: float = 9200.0,
                  alpha: float = 0.35,
                  k_spread: float = 1.5,
                  shipping: float = 0.5,
                  wind_mps: float = 5.0,
                  d_ref_m: float = 6000.0, 
                  P_ref_W: float = 15) -> float:
    """
    Potencia 'aproximada' (cota inferior física) para d<1500 m,
    anclada a P_ref_W=2.5 W en d_ref_m=1500 m.
    """
    B_hz = bandwidth_bpsk_rrc(Rb_bps, alpha)
    TL = tl_db(f_khz, d_m, k_spread)
    TL_ref = tl_db(f_khz, d_ref_m, k_spread)
    NLt = nl_total_db(f_khz, shipping, wind_mps, B_hz)
    NLt_ref = nl_total_db(f_khz, shipping, wind_mps, B_hz)
    delta = (TL - TL_ref) + (NLt - NLt_ref)  # dB
    return float(P_ref_W * (10.0 ** (delta/10.0)))

def p_tx_approx_W6000_65(d_m: float,
                  f_khz: float = 20.0,
                  Rb_bps: float = 9200.0,
                  alpha: float = 0.35,
                  k_spread: float = 1.5,
                  shipping: float = 0.5,
                  wind_mps: float = 5.0,
                  d_ref_m: float = 6000.0, 
                  P_ref_W: float = 65) -> float:
    """
    Potencia 'aproximada' (cota inferior física) para d<1500 m,
    anclada a P_ref_W=2.5 W en d_ref_m=1500 m.
    """
    B_hz = bandwidth_bpsk_rrc(Rb_bps, alpha)
    TL = tl_db(f_khz, d_m, k_spread)
    TL_ref = tl_db(f_khz, d_ref_m, k_spread)
    NLt = nl_total_db(f_khz, shipping, wind_mps, B_hz)
    NLt_ref = nl_total_db(f_khz, shipping, wind_mps, B_hz)
    delta = (TL - TL_ref) + (NLt - NLt_ref)  # dB
    return float(P_ref_W * (10.0 ** (delta/10.0)))


# ## comentar
# # Ejemplo: potencia aproximada en 10, 100, 500 m (anclada a 2.5 W @1500 m)
# for d in [0.1, 10, 100, 250, 500, 750, 1000, 1500]:
#     print(f"d={d:>4} m -> P_tx_aprox ≈ {p_tx_approx_W(d):10.10f} W")

# ##
# # Ejemplo: potencia aproximada en 10, 100, 500 m (anclada a 5 W @3000 m)
# for d3000 in [1501, 1750, 2000, 2500, 2750, 3000]:
#     print(f"d={d3000:>4} m -> P_tx_aprox ≈ {p_tx_approx_W3000(d3000):10.10f} W")

# ##
# # Ejemplo: potencia aproximada en 10, 100, 500 m (anclada a 15 W @6000 m)
# for d6000 in [3001, 3500, 4000, 4500, 5000, 5500, 6000]:
#     print(f"d={d6000:>4} m -> P_tx_aprox ≈ {p_tx_approx_W6000(d6000):10.10f} W")


# ##
# # Ejemplo: potencia aproximada en 10, 100, 500 m (anclada a 15 W @6000 m)
# for d6000_65 in [3001, 3500, 4000, 4500, 5000, 5500, 6000]:
#     print(f"d={d6000_65:>4} m -> P_tx_aprox ≈ {p_tx_approx_W6000_65(d6000_65):10.10f} W")

# # === Parámetros ===
# distances = np.linspace(1, 1500, 16)

# ##
# distances3000 = np.linspace(1500, 3000, 100)
# distances6000 = np.linspace(3000, 6000, 100)
# distances6000_65 = np.linspace(1, 6000, 100)
# ##

# p_eq = [p_tx_approx_W(d) for d in distances]
# ##
# p_eq3000 = [p_tx_approx_W3000(d3000) for d3000 in distances3000]
# p_eq6000 = [p_tx_approx_W6000(d6000) for d6000 in distances6000]
# p_eq6000_65 = [p_tx_approx_W6000_65(d6000_65) for d6000_65 in distances6000_65]
# ##

# p_real = np.full_like(distances, 2.5)  # consumo fijo escalonado
# ###
# p_real3000 = np.full_like(distances3000, 5.0)  # consumo fijo escalonado
# p_real6000 = np.full_like(distances6000, 15.0)  # consumo fijo escalonado
# p_real6000_65 = np.full_like(distances6000_65, 65.0)  # consumo fijo escalonado
# ##
# points = [(int(d), p_tx_approx_W(d)) for d in distances]

# latex_coords = " ".join([f"({d},{p:.6f})" for d,p in points])
# print(latex_coords)

# # === Gráfica ===
# plt.figure(figsize=(7,5))
# plt.plot(distances, p_eq, label="Consumo equivalente 1500 (cota inferior)", linewidth=2)
# ###
# # plt.plot(distances3000, p_eq3000, label="Consumo equivalente 3000 (cota inferior)", linewidth=2)
# # plt.plot(distances6000, p_eq6000, label="Consumo equivalente 6000 (cota inferior)", linewidth=2)
# # plt.plot(distances6000_65, p_eq6000_65, label="Consumo equivalente 6000 (cota inferior)", linewidth=2)
# ##
# plt.plot(distances, p_real, '--', label="Consumo real (fabricante, 2.5 W)", linewidth=2)
# ##
# # plt.plot(distances3000, p_real3000, '--', label="Consumo real (fabricante, 5 W)", linewidth=2)
# # plt.plot(distances6000, p_real6000, '--', label="Consumo real (fabricante, 15 W)", linewidth=2)
# # plt.plot(distances6000_65, p_real6000_65, '--', label="Consumo real (fabricante, 65 W)", linewidth=2)
# ##
# plt.xlabel("Distancia (m)")
# plt.ylabel("Potencia de transmisión (W)")
# plt.title("Comparación: consumo real vs. cota inferior ideal (d ≤ 1500 m)")
# plt.legend()
# plt.grid(True)
# plt.tight_layout()
# plt.show()