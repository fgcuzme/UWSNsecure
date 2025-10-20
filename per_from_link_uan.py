import math
import random
from path_loss import compute_path_loss
from noise_uan_aariza import compute_uan_noise
from curva_anclada_distancias_menores import p_tx_approx_W, bandwidth_bpsk_rrc

## Función para estimar BER/PER en BPSK/FSK y úsalo para alimentar la función anterior
def per_from_link(f_khz, distance_m, L, bitrate=9200, bw_hz=12420, spreading=1.5, EbN0_req_dB=7.0):
    p_tx = p_tx_approx_W(distance_m, f_khz, bitrate)
    # print(p_tx)
    SL_db = 170.8 + 10 * math.log10(p_tx)
    # SL_db = 170.8 + 10 * math.log10(2.5)
    # SL_db = 100
    #print("SL_db :", SL_db)
    
    tl_db, tl_lin = compute_path_loss(f_khz, distance_m, spread_coef=spreading)
    #print("tl_db : ", tl_db)
    nl_total_db, *_ = compute_uan_noise(f_khz, shipping=0.5, wind_speed_mps=5.0)
    # nl_total_db, *_ = compute_uan_noise(f_khz, shipping=1.0, wind_speed_mps=10.0)
    #print("nl_total_db :", nl_total_db)

    B = bandwidth_bpsk_rrc(Rb_bps=bitrate)
    #print("B : ", B)

    # SNR aproximado en banda (muy simple):
    # snr_db = - tl_db - nl_total_db  # si tuviéramos potencia y referencia de 1 µPa
    snr_db = SL_db - tl_db - nl_total_db  # si tuviéramos potencia y referencia de 1 µPa
    # print("snr_db :", snr_db)

    # Ajuste por energía por bit (modelo simplificado):
    EbN0_db = snr_db + 10*math.log10(bw_hz/bitrate)
    # EbN0_db = snr_db + 10 * math.log10(B / bitrate)
    # print("EbN0_db :", EbN0_db)

    # BER BPSK AWGN aprox:
    ber = ber_bpsk_awgn(EbN0_db)
    # ber = 0.5*math.erfc((10**(EbN0_db/10))**0.5 / math.sqrt(2))
    # ber = max(1e-5, 0.5 * math.erfc(math.sqrt(10**(EbN0_db / 10)) / math.sqrt(2)))
    # ber = max(1e-6, 0.5 * math.erfc(math.sqrt(10**(EbN0_db / 10)) / math.sqrt(2)))
    #print("ber :", ber)

    # PER para L bits
    #L = 1600  # o el paquete real
    per = 1 - (1 - ber)**L
    # print("per: ", per)
    return max(0.0, min(1.0, per)), SL_db, snr_db, EbN0_db, ber

def ber_bpsk_awgn(EbN0_db, floor=1e-10):
    ber = 0.5 * math.erfc(math.sqrt(10**(EbN0_db / 10)) / math.sqrt(2))
    return max(floor, ber)

def propagate_with_probability(per: float = 0.05, override_per: float = None) -> bool:
    """
    Devuelve True si el paquete llega (éxito), False si se pierde.
    - per: Packet Error Rate [0..1]
    - override_per: Si se especifica, se usa como PER fija en lugar del valor calculado
    Retorna:
    - True si el paquete se recibe (random >= PER), False si se pierde
    """
    # Usar PER fija si se proporciona
    effective_per = override_per if override_per is not None else per
    effective_per = max(0.0, min(1.0, effective_per))  # asegurar rango válido

    print("effective_per : ", effective_per)

    # per = max(0.0, min(1.0, per))
    # print("per : ", per)

    return random.random() >= effective_per


# for d in [100, 500, 1000, 1500, 2000, 2500, 3000]:
#     per, SL_db, snr_db, EbN0_db, ber = per_from_link(20, d, 4160)
#     print(f"Distancia: {d} m → PER: {per:.20f}, SNR: {snr_db:.2f} dB, Eb/N0: {EbN0_db:.2f} dB, BER: {ber:.2e}")

# per, SL_db, snr_db, EbN0_db, ber = per_from_link(f_khz=20, distance_m=1000, L=4160, bitrate=9200)
# print("per: ", per)

# p_tx = p_tx_approx_W(1000)
# print(f"P_tx @ 1000 m ≈ {p_tx:.4f} W")

# SL_db = 170.8 + 10 * math.log10(p_tx)
# print(f"SL ≈ {SL_db:.2f} dB re 1 µPa @ 1 m")

# f_khz=20.0

# tl_db, _ = compute_path_loss(f_khz, distance_m=1000, spread_coef=1.5)
# print(f"TL ≈ {tl_db:.2f} dB")

# nl_db, _ = compute_uan_noise(f_khz, shipping=0.5, wind_speed_mps=5.0)
# print(f"NL ≈ {nl_db:.2f} dB re 1 µPa²/Hz")

# B = bandwidth_bpsk_rrc(Rb_bps=9200.0)
# snr_db = SL_db - tl_db - nl_db
# EbN0_db = snr_db + 10 * math.log10(B / 9200.0)
# print(f"SNR ≈ {snr_db:.2f} dB | Eb/N0 ≈ {EbN0_db:.2f} dB")

# ber = 0.5 * math.erfc(math.sqrt(10**(EbN0_db / 10)) / math.sqrt(2))
# per = 1 - (1 - ber)**1600
# print(f"BER ≈ {ber:.10e} | PER ≈ {per:.20f}")