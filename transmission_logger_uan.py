# 📁 transmission_logger.py  —  CANÓNICO
import csv, os
from datetime import datetime
from math import dist as _dist

# === CSV canónico de eventos (una fila por evento de red/DAG) ===
EVENTS_CSV = os.environ.get("UWSN_EVENTS_CSV", "stats/transmissions.csv")

FIELDS = [
    "timestamp_iso","run_id","phase","module","msg_type",
    "sender_id","receiver_id","cluster_id",
    "distance_m",
    "latency_ms","lat_prop_ms","lat_tx_ms","lat_proc_ms","lat_dag_ms",
    "bits_sent","bits_received","success","packet_lost","energy_event_type",
    "energy_j","residual_energy_sender","residual_energy_receiver",
    "bitrate","SNR_dB","PER","freq_khz"
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
              snr_db=None, per=None,
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
        "bits_received": int(bits_received or 0),
        "success": bool(success),
        "packet_lost": bool(packet_lost),
        "energy_event_type": energy_event_type,
        "energy_j": round(float(energy_j or 0.0), 8),
        "residual_energy_sender": residual_sender,
        "residual_energy_receiver": residual_receiver,
        "bitrate": int(bitrate),
        "SNR_dB": round(snr_db,2), "PER": per,
        "freq_khz": float(freq_khz),
    }
    with open(csv_path, "a", newline="") as f:
        csv.DictWriter(f, fieldnames=FIELDS).writerow(row)




# === Wrappers legacy (compatibilidad) ===

def init_transmission_log(csv_path=EVENTS_CSV):
    _init(csv_path)

def log_transmission_event(sender_id, receiver_id, cluster_id, distance_m, latency_ms,
                           bits_sent, bits_received, packet_lost, success, energy_j,
                           shared_key_id, msg_type, csv_path=EVENTS_CSV):
    # Adaptador: mapear al canónico con campos mínimos (run_id/phase/module vacíos si no los pasan)
    _init(csv_path)
    with open(csv_path, "a", newline="") as f:
        csv.DictWriter(f, fieldnames=FIELDS).writerow({
            "timestamp_iso": datetime.utcnow().isoformat(),
            "run_id":"", "phase":"", "module":"legacy", "msg_type": msg_type,
            "sender_id": sender_id, "receiver_id": receiver_id, "cluster_id": cluster_id,
            "distance_m": round(distance_m or 0, 3),
            "latency_ms": round(latency_ms or 0, 2),
            "lat_prop_ms": 0, "lat_tx_ms": 0, "lat_proc_ms": 0, "lat_dag_ms": 0,
            "bits_sent": bits_sent or 0, "bits_received": bits_received or 0,
            "success": bool(success), "packet_lost": bool(packet_lost),
            "energy_j": round(energy_j or 0, 8),
            "residual_energy_sender": None, "residual_energy_receiver": None,
            "bitrate": None, "freq_khz": None
        })

def log_tangle_event(sender_id, receiver_id, cluster_id, latency_ms, energy_tx, energy_rx,
                     tx_type, phase, csv_path=EVENTS_CSV):
    _init(csv_path)
    with open(csv_path, "a", newline="") as f:
        csv.DictWriter(f, fieldnames=FIELDS).writerow({
            "timestamp_iso": datetime.utcnow().isoformat(),
            "run_id":"", "phase":"auth", "module":"tangle", "msg_type": f"{tx_type}:{phase}",
            "sender_id": sender_id, "receiver_id": receiver_id, "cluster_id": cluster_id,
            "distance_m": 0.0,
            "latency_ms": round(latency_ms or 0, 2),
            "lat_prop_ms": 0, "lat_tx_ms": 0, "lat_proc_ms": 0, "lat_dag_ms": 0,
            "bits_sent": 0, "bits_received": 0,
            "success": True, "packet_lost": False,
            "energy_j": round((energy_tx or 0) + (energy_rx or 0), 8),
            "residual_energy_sender": None, "residual_energy_receiver": None,
            "bitrate": None, "freq_khz": None
        })

def log_with_components(sender_id, receiver_id, cluster_id, distance_m,
                        lat_prop_ms, lat_tx_ms, lat_proc_ms, lat_dag_ms,
                        bits_sent, bits_received, success, energy_j,
                        msg_type, cpu_ms=None, sim_time_ms=None, csv_path=EVENTS_CSV):
    # Adaptador: vuelca en el formato canónico (ignora cpu_ms/sim_time_ms por simplicidad)
    _init(csv_path)
    latency_ms = (lat_prop_ms or 0) + (lat_tx_ms or 0) + (lat_proc_ms or 0) + (lat_dag_ms or 0)
    with open(csv_path, "a", newline="") as f:
        csv.DictWriter(f, fieldnames=FIELDS).writerow({
            "timestamp_iso": datetime.utcnow().isoformat(),
            "run_id":"", "phase":"", "module":"legacy", "msg_type": msg_type,
            "sender_id": sender_id, "receiver_id": receiver_id, "cluster_id": cluster_id,
            "distance_m": round(distance_m or 0, 3),
            "latency_ms": round(latency_ms, 2),
            "lat_prop_ms": round(lat_prop_ms or 0, 2),
            "lat_tx_ms": round(lat_tx_ms or 0, 2),
            "lat_proc_ms": round(lat_proc_ms or 0, 2),
            "lat_dag_ms": round(lat_dag_ms or 0, 2),
            "bits_sent": int(bits_sent or 0),
            "bits_received": int(bits_received or 0),
            "success": bool(success),
            "packet_lost": not bool(success),
            "energy_j": round(energy_j or 0, 8),
            "residual_energy_sender": None, "residual_energy_receiver": None,
            "bitrate": None, "freq_khz": None
        })



