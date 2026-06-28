# 📁 visualize_metrics.py

import json
import matplotlib.pyplot as plt
import os

def load_metrics(json_path="stats/simulation_metrics.json"):
    """Carga las métricas desde el archivo JSON."""
    with open(json_path, "r") as f:
        return json.load(f)

def plot_metric(data, ylabel, title, filename, color=None):
    """Genera un gráfico simple y lo guarda como imagen."""
    plt.figure()
    plt.plot(data, marker='o')
    plt.title(title)
    plt.xlabel("Transmisiones")
    plt.ylabel(ylabel)
    if color:
        plt.plot(data, color=color)
    plt.grid(True)
    output_path = os.path.join("stats", filename)
    plt.savefig(output_path)
    plt.close()
    print(f"📈 {title} guardado en {output_path}")

def visualize_all_metrics(json_path="stats/simulation_metrics.json"):
    """Crea gráficos para todas las métricas almacenadas."""
    metrics = load_metrics(json_path)

    if "latency" in metrics:
        plot_metric(metrics["latency"], "Latencia (ms)", "Latencia por Transmisión", "latency_plot.png")

    if "throughput" in metrics:
        plot_metric(metrics["throughput"], "Throughput (kbps)", "Tasa de Transmisión", "throughput_plot.png")

    if "energy_consumed" in metrics:
        plot_metric(metrics["energy_consumed"], "Energía (J)", "Consumo Energético", "energy_plot.png")

    if "packet_loss_percentage" in metrics:
        plt.figure()
        plt.bar(["Pérdida"], [metrics["packet_loss_percentage"]])
        plt.title("Pérdida Estimada de Paquetes")
        plt.ylabel("%")
        output_path = os.path.join("stats", "packet_loss_plot.png")
        plt.savefig(output_path)
        plt.close()
        print(f"📉 Pérdida de paquetes guardada en {output_path}")

    if "packet_loss" in metrics and metrics["packet_loss"]:
        plt.figure()
        plt.plot(metrics["packet_loss"], 'rx', label="Perdida")
        plt.title("Eventos de Pérdida de Paquetes")
        plt.xlabel("Transmisión")
        plt.ylabel("Pérdida (1=Sí, 0=No)")
        plt.grid(True)
        output_path = os.path.join("stats", "packet_loss_events_plot.png")
        plt.savefig(output_path)
        plt.close()
        print(f"📉 Evento de pérdida de paquetes guardado en {output_path}")

visualize_all_metrics()