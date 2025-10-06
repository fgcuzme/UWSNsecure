# 📁 transmission_summary.py — resumen sobre CSV canónico
import os, csv
import pandas as pd
from collections import defaultdict

CANON_CSV = os.environ.get("UWSN_EVENTS_CSV", "stats/transmissions.csv")

def summarize_per_node(input_csv=CANON_CSV, output_csv="stats/transmission_summary_per_node.csv"):
    if not os.path.exists(input_csv):
        print(f"🚨 Archivo no encontrado: {input_csv}")
        return
    df = pd.read_csv(input_csv)

    # Solo consideramos eventos de datos (puedes filtrar por phase/msg_type si quieres)
    # mask = df["msg_type"].astype(str).str.contains("DATA")
    mask = df["msg_type"].astype(str).str.contains("SYN:TDMA")
    d = df[mask].copy()

    summary = d.groupby("sender_id").agg(
        transmissions=("success","count"),
        successes=("success","sum"),
        latency_avg_ms=("latency_ms","mean"),
        energy_total_j=("energy_j","sum"),
        clusterId=("cluster_id","first"),
        packet_lost=("packet_lost","sum")
    ).reset_index()
    summary["packet_loss_percent"] = (summary["packet_lost"] / summary["transmissions"] * 100).round(2)
    summary["latency_avg_ms"] = summary["latency_avg_ms"].round(2)
    summary["energy_total_j"] = summary["energy_total_j"].round(8)
    summary = summary[["sender_id","clusterId","transmissions","successes","latency_avg_ms","energy_total_j","packet_loss_percent"]]
    os.makedirs(os.path.dirname(output_csv), exist_ok=True)
    summary.to_csv(output_csv, index=False)
    print(f"📁 Resumen por nodo exportado a {output_csv}")

def summarize_global(input_csv=CANON_CSV, output_csv="stats/transmission_summary_global.csv"):
    if not os.path.exists(input_csv):
        print(f"🚨 Archivo no encontrado: {input_csv}")
        return
    df = pd.read_csv(input_csv)
    # mask = df["msg_type"].astype(str).str.contains("DATA")
    mask = df["msg_type"].astype(str).str.contains("SYN:TDMA")
    d = df[mask].copy()

    total_tx = len(d)
    successful = int(d["success"].sum())
    avg_latency = d["latency_ms"].mean()
    total_energy = d["energy_j"].sum()
    avg_energy = d["energy_j"].mean()
    # Throughput efectivo (kbps) = sum(bits_recibidos) / sum(latency_ms)
    kbps = (d["bits_received"].sum()/1024.0) / (d["latency_ms"].sum()/1000.0) if d["latency_ms"].sum() > 0 else 0.0
    loss_pct = 100.0 * (1.0 - (successful / total_tx)) if total_tx>0 else 0.0

    os.makedirs(os.path.dirname(output_csv), exist_ok=True)
    with open(output_csv, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["total_transmissions","successful_receptions","avg_latency_ms","avg_throughput_kbps","total_energy_j","avg_energy_j","packet_loss_percent"])
        w.writerow([total_tx, successful, round(avg_latency or 0,2), round(kbps,2), round(total_energy or 0,8), round(avg_energy or 0,8), round(loss_pct,2)])
    print(f"📊 Resumen global exportado a {output_csv}")
