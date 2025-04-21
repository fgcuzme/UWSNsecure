# 📁 transmission_logger.py

import csv
import os
from datetime import datetime

# Ruta del archivo CSV
CSV_PATH = "stats/data_transmission_log.csv"

# Cabecera del CSV
CSV_FIELDS = [
    "timestamp",
    "sender_id",
    "receiver_id",
    "cluster_id",
    "distance_m",
    "latency_ms",
    "bits_sent",
    "bits_received",
    "packet_lost",
    "energy_j",
    "shared_key_id",
    "msg_type"
]

def init_transmission_log(csv_path=CSV_PATH):
    """Crea el archivo CSV si no existe y escribe el encabezado."""
    os.makedirs(os.path.dirname(csv_path), exist_ok=True)
    if not os.path.exists(csv_path):
        with open(csv_path, mode="w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=CSV_FIELDS)
            writer.writeheader()

def log_transmission_event(
    sender_id,
    receiver_id,
    cluster_id,
    distance_m,
    latency_ms,
    bits_sent,
    bits_received,
    packet_lost,
    energy_j,
    shared_key_id,
    msg_type,
    csv_path=CSV_PATH
):
    """Registra un evento de transmisión en el archivo CSV."""
    init_transmission_log(csv_path)

    with open(csv_path, mode="a", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_FIELDS)
        writer.writerow({
            "timestamp": datetime.utcnow().isoformat(),
            "sender_id": sender_id,
            "receiver_id": receiver_id,
            "cluster_id": cluster_id,
            "distance_m": round(distance_m, 2),
            "latency_ms": round(latency_ms, 2),
            "bits_sent": bits_sent,
            "bits_received": bits_received,
            "packet_lost": packet_lost,
            "energy_j": round(energy_j, 8),
            "shared_key_id": shared_key_id,
            "msg_type": msg_type
        })
