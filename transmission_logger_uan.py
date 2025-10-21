# 📁 transmission_logger.py  —  CANÓNICO
import csv, os, json, time, math, random
from datetime import datetime
from math import dist as _dist
from collections import defaultdict

# === CSV canónico de eventos (una fila por evento de red/DAG) ===
EVENTS_CSV = os.environ.get("UWSN_EVENTS_CSV", "stats/transmissions.csv")

FIELDS = [
    "timestamp_iso","run_id","phase","module","msg_type",
    "sender_id","receiver_id","cluster_id",
    "distance_m",
    "latency_ms","lat_prop_ms","lat_tx_ms","lat_proc_ms","lat_dag_ms",
    "bits_sent","bits_received","payload_len","success","packet_lost","energy_event_type",
    "energy_j","residual_energy_sender","residual_energy_receiver",
    "bitrate","SNR_dB","PER","freq_khz","SL_db", "EbN0_db", "BER"
]

def _init(csv_path: str):
    os.makedirs(os.path.dirname(csv_path), exist_ok=True)
    if not os.path.exists(csv_path):
        with open(csv_path, "w", newline="") as f:
            csv.DictWriter(f, fieldnames=FIELDS).writeheader()

def log_event(*,
              run_id, phase, module, msg_type,
              sender_id, receiver_id, cluster_id,
              start_pos, end_pos,
              bits_sent, bits_received,
              success, packet_lost,energy_event_type, energy_j,
              residual_sender=None, residual_receiver=None,
              bitrate=9200, freq_khz=20,
              lat_prop_ms=None, lat_tx_ms=None, lat_proc_ms=0.0, lat_dag_ms=0.0,
              snr_db=None, per=None, SL_db=None, EbN0_db=None, BER=None, payload_bits=None,
              csv_path: str = EVENTS_CSV):
    """
    Registro canónico de un evento.
    - Si lat_prop_ms / lat_tx_ms vienen None, se infiere distancia pero NO las latencias (déjalas calculadas por el main/módulo).
    """
    _init(csv_path)
    d_m = _dist(start_pos, end_pos)
    # latencias totales: si te pasan componentes, se suman; si no, usa 0 (el main debería calcularlas)
    lp = float(lat_prop_ms or 0.0)
    lt = float(lat_tx_ms or 0.0)
    lproc = float(lat_proc_ms or 0.0)
    ldag = float(lat_dag_ms or 0.0)
    latency_ms = lp + lt + lproc + ldag
    row = {
        "timestamp_iso": datetime.utcnow().isoformat(),
        "run_id": run_id, "phase": phase, "module": module, "msg_type": msg_type,
        "sender_id": int(sender_id), "receiver_id": int(receiver_id), "cluster_id": int(cluster_id) if cluster_id else None,
        "distance_m": round(d_m, 2),
        "latency_ms": round(latency_ms, 4),
        "lat_prop_ms": round(lp, 4),
        "lat_tx_ms": round(lt, 4),
        "lat_proc_ms": round(lproc, 4),
        "lat_dag_ms": round(ldag, 4),
        "bits_sent": int(bits_sent or 0),
        "payload_len": int(payload_bits or 0),
        "bits_received": int(bits_received or 0),
        "success": bool(success),
        "packet_lost": bool(packet_lost),
        "energy_event_type": energy_event_type,
        "energy_j": round(float(energy_j or 0.0), 8),
        "residual_energy_sender": residual_sender,
        "residual_energy_receiver": residual_receiver,
        "bitrate": int(bitrate),
        "SNR_dB": round(snr_db,2),
        "PER": per,
        "SL_db": round(SL_db,2),
        "EbN0_db": round(EbN0_db,2),
        "BER": BER,
        "freq_khz": float(freq_khz),
    }
    with open(csv_path, "a", newline="") as f:
        csv.DictWriter(f, fieldnames=FIELDS).writerow(row)
