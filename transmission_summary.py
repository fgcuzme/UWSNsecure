# 📁 transmission_summary.py

import csv
from collections import defaultdict
import os
import pandas as pd

def summarize_per_node(input_csv="stats/data_transmission_log.csv", output_csv="stats/transmission_summary_per_node.csv"):
    """Genera resumen de estadísticas por nodo emisor."""
    df = pd.read_csv(input_csv)

    summary = defaultdict(lambda: {
        "transmissions": 0,
        "successes": 0,
        "total_energy": 0.0,
        "latencies": [],
        "packets_lost": 0
    })

    for _, row in df.iterrows():
        sender = row["sender_id"]
        summary[sender]["transmissions"] += 1
        summary[sender]["total_energy"] += row["energy_j"]
        summary[sender]["latencies"].append(row["latency_ms"])
        if not row["packet_lost"]:
            summary[sender]["successes"] += 1
        else:
            summary[sender]["packets_lost"] += 1

    os.makedirs(os.path.dirname(output_csv), exist_ok=True)

    with open(output_csv, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([
            "node_id", "transmissions", "successes",
            "latency_avg_ms", "energy_total_j", "packet_loss_percent"
        ])
        for node_id, stats in summary.items():
            latency_avg = sum(stats["latencies"]) / len(stats["latencies"]) if stats["latencies"] else 0
            loss_pct = (stats["packets_lost"] / stats["transmissions"]) * 100 if stats["transmissions"] > 0 else 0
            writer.writerow([
                node_id,
                stats["transmissions"],
                stats["successes"],
                round(latency_avg, 2),
                round(stats["total_energy"], 8),
                round(loss_pct, 2)
            ])

    print(f"📁 Resumen por nodo exportado a {output_csv}")

def summarize_global(input_csv="stats/data_transmission_log.csv", output_csv="stats/transmission_summary_global.csv"):
    """Genera un resumen global de toda la simulación."""
    df = pd.read_csv(input_csv)

    total_tx = len(df)
    total_rx = df[~df["packet_lost"]].shape[0]
    avg_latency = df["latency_ms"].mean()
    avg_energy = df["energy_j"].mean()
    total_energy = df["energy_j"].sum()
    avg_throughput = (df["bits_received"].sum() / 1024) / (df["latency_ms"].sum() / 1000) if df["latency_ms"].sum() > 0 else 0
    loss_pct = 100 * (1 - total_rx / total_tx) if total_tx > 0 else 0

    os.makedirs(os.path.dirname(output_csv), exist_ok=True)

    with open(output_csv, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([
            "total_transmissions", "successful_receptions",
            "avg_latency_ms", "avg_throughput_kbps",
            "total_energy_j", "avg_energy_j", "packet_loss_percent"
        ])
        writer.writerow([
            total_tx, total_rx,
            round(avg_latency, 2),
            round(avg_throughput, 2),
            round(total_energy, 8),
            round(avg_energy, 8),
            round(loss_pct, 2)
        ])

    print(f"📊 Resumen global exportado a {output_csv}")
