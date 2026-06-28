# 📁 metrics.py

import time
import json

# Diccionario global que almacena todas las métricas
network_metrics = {
    "latency": [],
    "throughput": [],
    "energy_consumed": [],
    "packet_loss": [],
    "transmissions_successful": 0,
    "transmissions_total": 0
}

def log_latency(start_time, end_time):
    """Calcula y almacena la latencia en milisegundos."""
    latency_ms = (end_time - start_time) * 1000
    network_metrics["latency"].append(latency_ms)

def log_throughput(data_bytes, transmission_time):
    """Calcula y almacena el throughput en kbps."""
    if transmission_time > 0:
        throughput_kbps = (data_bytes / 1024) / transmission_time
        network_metrics["throughput"].append(throughput_kbps)

def log_energy(bits_sent, bits_received):
    """Calcula el consumo energético estimado."""
    E_tx = bits_sent * 5e-9  # J/bit para transmisión
    E_rx = bits_received * 1e-9  # J/bit para recepción
    network_metrics["energy_consumed"].append(E_tx + E_rx)

# def log_packet_result(successful: bool):
#     """Actualiza los contadores de paquetes enviados y recibidos."""
#     network_metrics["transmissions_total"] += 1
#     if successful:
#         network_metrics["transmissions_successful"] += 1

def log_packet_result(successful: bool):
    """Actualiza contadores y guarda pérdida por evento."""
    network_metrics["transmissions_total"] += 1
    if successful:
        network_metrics["transmissions_successful"] += 1
        network_metrics["packet_loss"].append(0)
    else:
        network_metrics["packet_loss"].append(1)  # Marca de pérdida


def get_packet_loss_percentage():
    """Calcula el porcentaje estimado de pérdida de paquetes."""
    total = network_metrics["transmissions_total"]
    success = network_metrics["transmissions_successful"]
    return (1 - success / total) * 100 if total > 0 else 0

def summarize_metrics():
    """Imprime métricas agregadas en consola."""
    def avg(lst): return sum(lst) / len(lst) if lst else 0

    print("\n📊 MÉTRICAS DE SIMULACIÓN:")
    print(f"🔁 Total transmisiones: {network_metrics['transmissions_total']}")
    print(f"✅ Transmisiones exitosas: {network_metrics['transmissions_successful']}")
    print(f"❌ Pérdida estimada: {get_packet_loss_percentage():.2f}%")
    print(f"⏱️ Latencia promedio: {avg(network_metrics['latency']):.2f} ms")
    print(f"⚡ Energía promedio consumida: {avg(network_metrics['energy_consumed']):.6f} J")
    print(f"🚀 Throughput promedio: {avg(network_metrics['throughput']):.2f} kbps")

def export_metrics_to_json(filepath="stats/simulation_metrics.json"):
    """Exporta métricas en formato JSON para análisis externo."""
    export_data = network_metrics.copy()
    export_data["packet_loss_percentage"] = get_packet_loss_percentage()

    with open(filepath, "w") as f:
        json.dump(export_data, f, indent=4)

    print(f"📁 Métricas exportadas a {filepath}")


# 📁 metrics_exporter.py

import csv
import os
# from metrics import network_metrics, get_packet_loss_percentage

def export_metrics_to_csv(csv_path="stats/metrics_summary.csv"):
    """Agrega un resumen de métricas al CSV acumulativo."""

    def avg(lst): return sum(lst) / len(lst) if lst else 0

    headers = [
        "latency_avg_ms",
        "throughput_avg_kbps",
        "energy_avg_j",
        "packet_loss_percent",
        "total_transmissions",
        "successful_transmissions"
    ]

    row = [
        round(avg(network_metrics["latency"]), 2),
        round(avg(network_metrics["throughput"]), 2),
        round(avg(network_metrics["energy_consumed"]), 6),
        round(get_packet_loss_percentage(), 2),
        network_metrics["transmissions_total"],
        network_metrics["transmissions_successful"]
    ]

    os.makedirs(os.path.dirname(csv_path), exist_ok=True)
    write_header = not os.path.exists(csv_path)

    with open(csv_path, mode="a", newline="") as file:
        writer = csv.writer(file)
        if write_header:
            writer.writerow(headers)
        writer.writerow(row)

    print(f"📄 Métricas resumidas exportadas en {csv_path}")
