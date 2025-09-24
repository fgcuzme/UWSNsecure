# validate_snr_viability.py
import numpy as np
from typing import List, Dict, Tuple
from path_loss import compute_path_loss                           # Paso (1): TL(d,f)
from noise_uan_aariza import compute_uan_noise                    # Paso (1): NL_psd(f)


# =========================
# Parámetros generales
# =========================
FREQUENCY_KHZ = 20.0                    # f (kHz)
SPREAD_COEF   = 1.5                     # coef. de dispersión geométrica
SHIPPING      = 0.5                     # [0..1] tráfico marítimo
WIND_MPS      = 5.0                     # viento (m/s)

R_B_BPS       = 9200.0                  # tasa de bits (bps)
ALPHA_ROLL    = 0.35                    # roll-off RRC para BPSK
B_HZ          = R_B_BPS * (1.0 + ALPHA_ROLL)  # Paso (2): B ≈ Rb (1+α)

# Niveles de potencia ELÉCTRICA (escalonados del fabricante)
# TX_LEVELS_W   = [0.000010, 0.0115, 0.0717, 0.1862, 0.3728, 0.8462, 2.5, 5.0, 15.0, 65.0]  # W   0.000010@1m; 0.0115@100m; 0.0717@300m; 0.1862@500m; 0.3728@700m; 0.8462@1000m
TX_LEVELS_W   = [2.5, 5.0, 15.0, 65.0]  # W 

# Otros parámetros del presupuesto de enlace
ETA_PA        = 0.30                    # eficiencia PA (eléctrico→acústico)
DI_TX_DB      = 0.0                     # directividad TX (dB)
DI_RX_DB      = 0.0                     # directividad RX (dB)
G_PROC_DB     = 0.0                     # ganancia de procesamiento (dB)
MARGIN_DB     = 3.0                     # margen de diseño (dB)

# SNR mínimo objetivo (elige según BER objetivo y FEC)
# Aproximaciones típicas BPSK en AWGN:
#   BER=1e-3  => Eb/N0 ≈  6.8 dB
#   BER=1e-5  => Eb/N0 ≈  9.6 dB
EBN0_DB       = 16 # 9.6                # p.ej. BER≈1e-5
FEC_GAIN_DB   = 0.0                     # ganancia de codificación (si aplica)
SNR_MIN_DB    = EBN0_DB + 10*np.log10(R_B_BPS / B_HZ) - FEC_GAIN_DB + MARGIN_DB

def sl_from_electric_power(P_tx_elec_W: float, eta_pa: float = ETA_PA, di_tx_db: float = DI_TX_DB) -> float:
    """
    Paso (4): Convertir P_tx (eléctrica) -> SL (dB re 1 µPa @ 1 m).
    P_ac = eta * P_tx ;  SL ≈ 170.8 + 10log10(P_ac) + DI_tx
    """
    P_ac_W = eta_pa * P_tx_elec_W
    SL_dB  = 170.8 + 10.0*np.log10(P_ac_W) + di_tx_db
    # SL_dB  = 171.5 + 10.0*np.log10(P_ac_W) + di_tx_db
    return float(SL_dB)

def nl_total_db(frequency_khz: float, shipping: float, wind_mps: float, B_hz: float) -> Tuple[float, float]:
    """
    Paso (1) y (3): NL_psd (dB re 1 µPa²/Hz) y NL_tot = NL_psd + 10log10(B)
    """
    nl_psd_db, _ = compute_uan_noise(frequency_khz, shipping, wind_mps)
    print("NL : ", nl_psd_db)
    nl_tot_db = float(nl_psd_db + 10.0*np.log10(B_hz))
    return float(nl_psd_db), nl_tot_db

def tl_db(frequency_khz: float, distance_m: float, spread_coef: float) -> float:
    """
    Paso (1): TL(d,f) en dB (dispersión geométrica + absorción)
    """
    tl, _ = compute_path_loss(frequency_khz, distance_m, spread_coef)
    return float(tl)

def snr_achievable_db(
    distance_m: float,
    P_tx_elec_W: float,
    frequency_khz: float = FREQUENCY_KHZ,
    spread_coef: float = SPREAD_COEF,
    shipping: float = SHIPPING,
    wind_mps: float = WIND_MPS,
    B_hz: float = B_HZ,
    eta_pa: float = ETA_PA,
    di_tx_db: float = DI_TX_DB,
    di_rx_db: float = DI_RX_DB,
    g_proc_db: float = G_PROC_DB,
    margin_db: float = MARGIN_DB
) -> Dict[str, float]:
    """
    Paso (5): SNR(d) = SL - TL - NL_tot + DI_rx + G_proc - Margen
    """
    SL_dB        = sl_from_electric_power(P_tx_elec_W, eta_pa=eta_pa, di_tx_db=di_tx_db)
    TL_dB        = tl_db(frequency_khz, distance_m, spread_coef)
    NL_psd_dB, NL_tot_dB = nl_total_db(frequency_khz, shipping, wind_mps, B_hz)
    RL_dB        = SL_dB - TL_dB
    SNR_dB       = RL_dB - NL_tot_dB + di_rx_db + g_proc_db - margin_db
    return {
        "SL_dB": SL_dB,
        "TL_dB": TL_dB,
        "NL_psd_dB": NL_psd_dB,
        "NL_tot_dB": NL_tot_dB,
        "RL_dB": RL_dB,
        "SNR_dB": SNR_dB
    }

def validate_link_for_distances(
    distances_m: List[float],
    tx_levels_W: List[float] = TX_LEVELS_W,
    snr_min_db: float = SNR_MIN_DB,
    **kwargs
) -> List[Dict[str, float]]:
    """
    Ejecuta el procedimiento (1→5) para cada distancia y cada nivel de potencia escalonado:
      1) TL(d,f) y NL_psd(f)
      2) B ≈ Rb(1+α) (aquí ya está fijado en B_HZ)
      3) NL_tot = NL_psd + 10log10(B)
      4) P_tx -> SL (vía eficiencia y directividad)
      5) SNR(d) y comparación con SNR_min
    """
    results = []
    for d in distances_m:
        for P_elec in tx_levels_W:
            met = snr_achievable_db(distance_m=d, P_tx_elec_W=P_elec, **kwargs)
            results.append({
                "distance_m": float(d),
                "P_tx_W": float(P_elec),
                "SNR_dB": float(met["SNR_dB"]),
                "meets_SNRmin": bool(met["SNR_dB"] >= snr_min_db),
                "SNR_min_dB": float(snr_min_db),
                "SL_dB": float(met["SL_dB"]),
                "TL_dB": float(met["TL_dB"]),
                "NL_psd_dB": float(met["NL_psd_dB"]),
                "NL_tot_dB": float(met["NL_tot_dB"]),
                "B_hz": float(kwargs.get("B_hz", B_HZ)),
            })
    return results

# ====== Ejemplo de uso ======
if __name__ == "__main__":
    distances = [1, 100, 300, 500, 700, 1000, 1500, 3000, 6000, 8000]  # enlaces a verificar
    results = validate_link_for_distances(distances_m=distances)

    # Resumen: para cada distancia, mínima potencia que cumple SNR_min
    from collections import defaultdict
    best = defaultdict(lambda: None)
    for r in results:
        if r["meets_SNRmin"]:
            d = r["distance_m"]
            prev = best[d]
            if prev is None or r["P_tx_W"] < prev["P_tx_W"]:
                best[d] = r

    print(f"Parámetros: f={FREQUENCY_KHZ} kHz, α={ALPHA_ROLL}, B≈{B_HZ:.0f} Hz, SNR_min≈{SNR_MIN_DB:.2f} dB")
    for d in distances:
        cand = best[d]
        if cand:
            print(f"d={d:>5.0f} m → cumple con P_tx={cand['P_tx_W']:>5.6f} W | SNR={cand['SNR_dB']:.2f} dB (SL={cand['SL_dB']:.2f} dB, TL={cand['TL_dB']:.2f} dB, NLtot={cand['NL_tot_dB']:.2f} dB)")
        else:
            print(f"d={d:>5.0f} m → NO factible ni con 65 W (SNR_min={SNR_MIN_DB:.2f} dB)")
