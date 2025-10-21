# 📁 transmission_summary.py — resumen sobre CSV canónico
import os, csv
import pandas as pd
from collections import defaultdict

# # PHASE = "syn"
# PHASE = "auth"
# # PHASE = "data"

CANON_CSV = os.environ.get("UWSN_EVENTS_CSV", "stats/transmissions.csv")

# def summarize_per_node(input_csv=CANON_CSV, output_csv=f"stats/transmission_summary_per_node_{PHASE}.csv"):
#     if not os.path.exists(input_csv):
#         print(f"🚨 Archivo no encontrado: {input_csv}")
#         return
#     df = pd.read_csv(input_csv)

#     # Solo consideramos eventos de datos (puedes filtrar por phase/msg_type si quieres)
#     # mask = df["msg_type"].astype(str).str.contains("DATA")
#     mask = df["phase"].astype(str).str.contains(PHASE)
#     # mask = df["msg_type"].astype(str).str.contains("SYN:TDMA")
#     d = df[mask].copy()

#     # Separar eventos TX y RX
#     tx = d[d["energy_event_type"] == "tx"]
#     rx = d[d["energy_event_type"] == "rx"]

#     print(tx)
#     print(rx)

#     tx_summary = tx.groupby("sender_id").agg(
#         transmissions=("success","count"),
#         successes=("success","sum"),
#         latency_avg_ms=("latency_ms","mean"),
#         energy_tx_j=("energy_j","sum"),
#         clusterId=("cluster_id","first"),
#         packet_lost=("packet_lost","sum")
#     ).reset_index().rename(columns={"sender_id": "node_id"})

#     print(tx_summary)

#     rx_summary = rx.groupby("receiver_id").agg(
#         # transmissions_rx=("success","count"),
#         # successes_rx=("success","sum"),
#         # latency_avg_ms_rx=("latency_ms","mean"),
#         energy_rx_j=("energy_j","sum")
#         # clusterId=("cluster_id","first"),
#         # packet_lost_tx=("packet_lost","sum")
#     ).reset_index().reset_index().rename(columns={"receiver_id": "node_id"})
#     print(rx_summary)

#     # Combinar ambos por nodo
#     summary = pd.merge(tx_summary, rx_summary, on="node_id", how="outer")
#     summary["energy_tx_j"] = summary["energy_tx_j"].fillna(0.0)
#     summary["energy_rx_j"] = summary["energy_rx_j"].fillna(0.0)
#     summary["energy_total_j"] = summary["energy_tx_j"] + summary["energy_rx_j"]
#     summary["latency_avg_ms"] = summary["latency_avg_ms"].round(2)
#     summary["energy_tx_j"] = summary["energy_tx_j"].round(8)
#     summary["energy_rx_j"] = summary["energy_rx_j"].round(8)
#     summary["energy_total_j"] = summary["energy_total_j"].round(8)
#     summary["packet_loss_percent"] = (summary["packet_lost"] / summary["transmissions"] * 100).round(2)
#     # Selección final de columnas
#     summary = summary[[
#         "node_id", "clusterId", "transmissions", "successes",
#         "latency_avg_ms", "energy_tx_j", "energy_rx_j", "energy_total_j",
#         "packet_loss_percent"
#     ]]
    
#     os.makedirs(os.path.dirname(output_csv), exist_ok=True)
#     summary.to_csv(output_csv, index=False)
#     print(f"📁 Resumen por nodo exportado a {output_csv}")

# def summarize_global(input_csv=CANON_CSV, output_csv=f"stats/transmission_summary_global_{PHASE}.csv"):
#     if not os.path.exists(input_csv):
#         print(f"🚨 Archivo no encontrado: {input_csv}")
#         return
#     df = pd.read_csv(input_csv)
#     # mask = df["msg_type"].astype(str).str.contains("DATA")
#     mask = df["phase"].astype(str).str.contains(PHASE)

#     # mask = df["msg_type"].astype(str).str.contains("SYN:TDMA")
#     d = df[mask].copy()

#     # Calcular payload_bits (solo si existe payload_len)
#     if "payload_len" in d.columns:
#         d["payload_bits"] = d["payload_len"].fillna(0).astype(int) * 8
#     else:
#         d["payload_bits"] = 0

#     total_tx = len(d)
#     successful = int(d["success"].sum())
#     avg_latency = d["latency_ms"].mean()
#     total_energy = d["energy_j"].sum()
#     avg_energy = d["energy_j"].mean()
#     # Throughput efectivo (kbps) = sum(bits_recibidos) / sum(latency_ms)
#     # kbps = (d["bits_received"].sum()/1024.0) / (d["latency_ms"].sum()/1000.0) if d["latency_ms"].sum() > 0 else 0.0
#     # Throughput bruto (kbps)
#     kbps_bruto = (d["bits_received"].sum()/1024.0) / (d["latency_ms"].sum()/1000.0) if d["latency_ms"].sum() > 0 else 0.0
#     # Throughput útil (solo payload)
#     kbps_util = (d["payload_bits"].sum()/1024.0) / (d["latency_ms"].sum()/1000.0) if d["latency_ms"].sum() > 0 else 0.0
#     # Eficiencia relativa
#     eff_pct = (d["payload_bits"].sum() / d["bits_received"].sum() * 100.0) if d["bits_received"].sum() > 0 else 0.0

#     loss_pct = 100.0 * (1.0 - (successful / total_tx)) if total_tx>0 else 0.0

#     os.makedirs(os.path.dirname(output_csv), exist_ok=True)
#     with open(output_csv, "w", newline="") as f:
#         w = csv.writer(f)
#         # w.writerow(["total_transmissions","successful_receptions","avg_latency_ms","avg_throughput_kbps","total_energy_j","avg_energy_j","packet_loss_percent"])
#         # w.writerow([total_tx, successful, round(avg_latency or 0,2), round(kbps,2), round(total_energy or 0,8), round(avg_energy or 0,8), round(loss_pct,2)])
#         w.writerow([
#         "total_transmissions","successful_receptions","avg_latency_ms",
#         "avg_throughput_bruto_kbps","avg_throughput_util_kbps",
#         "efficiency_percent","total_energy_j","avg_energy_j","packet_loss_percent"
#         ])
#         w.writerow([
#             total_tx, successful, round(avg_latency or 0,2),
#             round(kbps_bruto,2), round(kbps_util,2),
#             round(eff_pct,2), round(total_energy or 0,8),
#             round(avg_energy or 0,8), round(loss_pct,2)
#         ])
#     print(f"📊 Resumen global exportado a {output_csv}")


# # Resumen y PROYECCIÓN
# summarize_per_node()
# summarize_global()

PHASES = ["syn", "auth", "data"]

def summarize_per_node_by_run(input_csv=CANON_CSV, output_dir=None, phase=None):
    if not os.path.exists(input_csv):
        print(f"🚨 Archivo no encontrado: {input_csv}")
        return
    df = pd.read_csv(input_csv)
    df = df[df["phase"].astype(str).str.contains(phase)]
    # df = df[df["phase"].astype(str).str.strip().str.lower() == phase.lower()]

    output_dir = output_dir or os.environ.get("OUTPUT_DIR", "stats/")
    # os.makedirs(output_dir, exist_ok=True)

    for run_id, group in df.groupby("run_id"):
        tx = group[group["energy_event_type"] == "tx"]
        rx = group[group["energy_event_type"] == "rx"]

        tx_summary = tx.groupby("sender_id").agg(
            transmissions=("success", "count"),
            successes=("success", "sum"),
            latency_avg_ms=("latency_ms", "mean"),
            energy_tx_j=("energy_j", "sum"),
            clusterId=("cluster_id", "first"),
            packet_lost=("packet_lost", "sum")
        ).reset_index().rename(columns={"sender_id": "node_id"})

        rx_summary = rx.groupby("receiver_id").agg(
            energy_rx_j=("energy_j", "sum")
        ).reset_index().rename(columns={"receiver_id": "node_id"})

        summary = pd.merge(tx_summary, rx_summary, on="node_id", how="outer")
        summary["energy_tx_j"] = summary["energy_tx_j"].fillna(0.0)
        summary["energy_rx_j"] = summary["energy_rx_j"].fillna(0.0)
        summary["energy_total_j"] = summary["energy_tx_j"] + summary["energy_rx_j"]
        summary["latency_avg_ms"] = summary["latency_avg_ms"].round(2)
        summary["energy_tx_j"] = summary["energy_tx_j"].round(8)
        summary["energy_rx_j"] = summary["energy_rx_j"].round(8)
        summary["energy_total_j"] = summary["energy_total_j"].round(8)
        summary["packet_loss_percent"] = (summary["packet_lost"] / summary["transmissions"] * 100).round(2)

        summary = summary[[
            "node_id", "clusterId", "transmissions", "successes",
            "latency_avg_ms", "energy_tx_j", "energy_rx_j", "energy_total_j",
            "packet_loss_percent"
        ]]

        output_csv = os.path.join(output_dir, f"{run_id}_{phase}_per_node.csv")
        summary.to_csv(output_csv, index=False)
        print(f"📁 Resumen por nodo exportado: {output_csv}")


def summarize_global_by_run(input_csv=CANON_CSV, output_dir=None, phase=None):
    if not os.path.exists(input_csv):
        print(f"🚨 Archivo no encontrado: {input_csv}")
        return
    df = pd.read_csv(input_csv)
    df = df[df["phase"].astype(str).str.contains(phase)]
    # df = df[df["phase"].astype(str).str.strip().str.lower() == phase.lower()]

    output_dir = output_dir or os.environ.get("OUTPUT_DIR", "stats/")
    # os.makedirs(input_csv, exist_ok=True)

    for run_id, group in df.groupby("run_id"):
        d = group.copy()

        if "payload_len" in d.columns:
            d["payload_bits"] = d["payload_len"].fillna(0).astype(int) * 8
        else:
            d["payload_bits"] = 0
        
        # - PDR desde el punto de vista del receptor: rx_success / tx_total - recepción exitosa (paquete válido, sin errores)
        # - Tasa de entrega efectiva desde el emisor: tx_success / tx_total -  transmisión que fue confirmada como entregada (por ACK o por log cruzado)
        # tx_events = df[df.energy_event_type == "tx"]
        # rx_events = df[df.energy_event_type == "rx"]

        # tx_success = tx_events["success"].sum()
        # rx_success = rx_events["success"].sum()

        tx_events = d[d["energy_event_type"] == "tx"]
        total_tx = len(tx_events)
        rx_events = d[d.energy_event_type == "rx"]
        successful = int(rx_events["success"].sum())

        avg_latency = d["latency_ms"].mean()
        total_energy = d["energy_j"].sum()
        avg_energy = d["energy_j"].mean()

        kbps_bruto = (d["bits_received"].sum()/1024.0) / (d["latency_ms"].sum()/1000.0) if d["latency_ms"].sum() > 0 else 0.0
        kbps_util = (d["payload_bits"].sum()/1024.0) / (d["latency_ms"].sum()/1000.0) if d["latency_ms"].sum() > 0 else 0.0
        eff_pct = (d["payload_bits"].sum() / d["bits_received"].sum() * 100.0) if d["bits_received"].sum() > 0 else 0.0
        loss_pct = 100.0 * (1.0 - (successful / total_tx)) if total_tx > 0 else 0.0

        output_csv = os.path.join(output_dir, f"{run_id}_{phase}_global.csv")
        with open(output_csv, "w", newline="") as f:
            w = csv.writer(f)
            w.writerow([
                "run_id", "total_transmissions", "successful_receptions", "avg_latency_ms",
                "avg_throughput_bruto_kbps", "avg_throughput_util_kbps",
                "efficiency_percent", "total_energy_j", "avg_energy_j", "packet_loss_percent"
            ])
            w.writerow([
                run_id, total_tx, successful, round(avg_latency or 0,2),
                round(kbps_bruto,2), round(kbps_util,2),
                round(eff_pct,2), round(total_energy or 0,8),
                round(avg_energy or 0,8), round(loss_pct,2)
            ])
        print(f"📊 Resumen global exportado: {output_csv}")

import time
output_dir = os.environ.get("OUTPUT_DIR", "stats/")
for phase in PHASES:
    print(f"\n📡 Procesando fase: {phase}")
    summarize_per_node_by_run(phase=phase)
    summarize_global_by_run(phase=phase)