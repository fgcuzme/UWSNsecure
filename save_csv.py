import csv
import os

# Guardar estadísticas en un archivo CSV
def save_stats_to_csv(filename, stats, method_name):
    """
    Guarda las estadísticas del proceso de sincronización en un archivo CSV.
    
    Parámetros:
    filename: El nombre del archivo CSV donde se guardarán las estadísticas.
    stats: Diccionario que contiene las estadísticas del proceso.
    method_name: Nombre del método (TDMA o CDMA) para incluir en las estadísticas.
    """
    # Obtener la ruta del directorio donde se encuentra el script actual
    # current_dir = os.path.dirname(os.path.abspath(__file__))
    current_dir = os.getcwd()

    # Definir la carpeta 'stats'
    files_stats = os.path.join(current_dir, 'stats')

    # Crea la carpeta en caso de no existir
    if not os.path.exists(files_stats):
        os.makedirs(files_stats)

    # Ruta completa del archivo de estadísticas dentro de la carpeta 'stats'
    ruta_stats = os.path.join(files_stats, filename)

    # Escribir encabezados y datos en el archivo CSV
    with open(ruta_stats, mode='a', newline='') as file:
        writer = csv.writer(file)
        
        # Si el archivo está vacío, escribir los encabezados
        if file.tell() == 0:
            writer.writerow(['Method', 'Sync Success', 'Sync Failures', 'Total Retransmissions', 'Total Energy Consumed', 'Average Sync Time'])

        # Escribir los datos de las estadísticas
        avg_sync_time = sum(stats['sync_times']) / len(stats['sync_times']) if len(stats['sync_times']) > 0 else 0
        writer.writerow([
            method_name,
            stats['sync_success'],
            stats['sync_failures'],
            stats['total_retransmissions'],
            stats['total_energy_consumed'],
            avg_sync_time
        ])

# # Llamar a la función después del proceso de sincronización TDMA
# save_stats_to_csv('sync_stats.csv', stats_tdma, 'TDMA')

# # Llamar a la función después del proceso de sincronización CDMA
# save_stats_to_csv('sync_stats.csv', stats_cdma, 'CDMA')



def save_stats_to_csv_cdma(filename, stats, method_name):
    """
    Guarda las estadísticas del proceso de sincronización en un archivo CSV.
    
    Parámetros:
    filename: El nombre del archivo CSV donde se guardarán las estadísticas.
    stats: Diccionario que contiene las estadísticas del proceso.
    method_name: Nombre del método (TDMA o CDMA) para incluir en las estadísticas.
    """

    # Obtener la ruta del directorio donde se encuentra el script actual
    # current_dir = os.path.dirname(os.path.abspath(__file__))
    current_dir = os.getcwd()

    # Definir la carpeta 'stats'
    files_stats = os.path.join(current_dir, 'stats')

    # Crea la carpeta en caso de no existir
    if not os.path.exists(files_stats):
        os.makedirs(files_stats)

    # Ruta completa del archivo de estadísticas dentro de la carpeta 'stats'
    ruta_stats = os.path.join(files_stats, filename)

    # Escribir encabezados y datos en el archivo CSV
    with open(ruta_stats, mode='a', newline='') as file:
        writer = csv.writer(file)
        
        # Si el archivo está vacío, escribir los encabezados
        if file.tell() == 0:
            writer.writerow(['Method', 'Sync Success', 'Sync Failures', 'Total Retransmissions', 'Total Energy Consumed', 'Total Energy Listen', 'Average Sync Time'])

        # Escribir los datos de las estadísticas
        avg_sync_time = sum(stats['sync_times']) / len(stats['sync_times']) if len(stats['sync_times']) > 0 else 0
        writer.writerow([
            method_name,
            stats['sync_success'],
            stats['sync_failures'],
            stats['total_retransmissions'],
            stats['total_energy_consumed'],
            stats['total_energy_listen'],  # Registrar consumo de energía por escucha
            avg_sync_time
        ])

# # Guardar estadísticas de CDMA
# save_stats_to_csv('sync_stats.csv', stats_cdma, 'CDMA')


# Guardar estadisticas de Tx

def save_stats_tx(filename, stats_tx):
    """
    Guarda las estadísticas de las transacciones en un archivo CSV.

    stats_tx: Diccionario que contiene las estadísticas de las transacciones (como tiempos de creación, verificación y respuesta).
    archivo_csv: Nombre del archivo CSV donde se guardarán los datos.
    """
    
    # Obtener la ruta del directorio donde se encuentra el script actual
    #current_dir = os.path.dirname(os.path.abspath(__file__))
    current_dir = os.getcwd()

    # Definir la carpeta 'stats'
    files_stats = os.path.join(current_dir, 'stats')

    # Crea la carpeta en caso de no existir
    if not os.path.exists(files_stats):
        os.makedirs(files_stats)

    # Ruta completa del archivo de estadísticas dentro de la carpeta 'stats'
    ruta_stats = os.path.join(files_stats, filename)
    
    # Crear o abrir el archivo CSV en modo escritura
    with open(ruta_stats, mode='a', newline='') as file:
        writer = csv.writer(file)

        # Escribir los encabezados en el archivo CSV
        # Si el archivo está vacío, escribir los encabezados
        if file.tell() == 0:
            writer.writerow(['Times CreateTxGen', 'times_propagation_txgen', 'times_verifyTx_toCH', 'times_TxresponseCH', 'times_propagation_response_tx'])

        # Convertir las estadísticas en filas y escribirlas en el archivo
        for i in range(len(stats_tx['times_createTxgen'])):
            writer.writerow([
                stats_tx['times_createTxgen'][i],
                stats_tx['times_propagation_txgen'][i] if i < len(stats_tx['times_propagation_txgen']) else '',
                stats_tx['times_verifyTx_toCH'][i] if i < len(stats_tx['times_verifyTx_toCH']) else '',
                stats_tx['times_TxresponseCH'][i] if i < len(stats_tx['times_TxresponseCH']) else '',
                stats_tx['times_propagation_response_tx'][i] if i < len(stats_tx['times_propagation_response_tx']) else ''
            ])



def save_stats_to_syn_csv(file_name, stats, method_name):
    """
    Guarda las estadísticas de sincronización en un archivo CSV.

    Parámetros:
    - file_name: Nombre del archivo CSV.
    - stats: Diccionario de estadísticas que contiene datos de CHs y nodos.
    """
    
    # Obtener la ruta actual y definir la carpeta 'stats' para guardar el archivo
    current_dir = os.getcwd()
    files_stats = os.path.join(current_dir, 'stats')
    
    # Crear la carpeta si no existe
    if not os.path.exists(files_stats):
        os.makedirs(files_stats)

    # Ruta completa del archivo dentro de la carpeta 'stats'
    ruta_stats = os.path.join(files_stats, file_name)

    # Escribir en el archivo CSV
    with open(ruta_stats, mode='a', newline='') as file:
        writer = csv.writer(file)
        
        # Escribir encabezados si el archivo está vacío
        if file.tell() == 0:
            writer.writerow([
                'ID', 'Tipo', 'Energía Consumida (J)', 
                'Tiempo de Sincronización (s)', 'Retransmisiones', 'IsSynStatus'
            ])
        
        # Escribir las estadísticas de cada CH y nodo en el archivo
        for key, value in stats["sync_stats"].items():
            writer.writerow([
                method_name,
                key, 
                "CH" if "CH" in key else "Nodo",
                value.get("energy_consumed", ''),
                value.get("sync_time", ''),
                value.get("retransmissions", ''),
                value.get("is_syn", '')
            ])

    print(f"Estadísticas guardadas en: {ruta_stats}")



def save_stats_energy_proTx_csv(file_name, stats):
    """
    Guarda las estadísticas de sincronización en un archivo CSV.

    Parámetros:
    - file_name: Nombre del archivo CSV.
    - stats: Diccionario de estadísticas que contiene datos de CHs y nodos.
    """
    
    # Obtener la ruta actual y definir la carpeta 'stats' para guardar el archivo
    current_dir = os.getcwd()
    files_stats = os.path.join(current_dir, 'stats')
    
    # Crear la carpeta si no existe
    if not os.path.exists(files_stats):
        os.makedirs(files_stats)

    # Ruta completa del archivo dentro de la carpeta 'stats'
    ruta_stats = os.path.join(files_stats, file_name)

    # Escribir en el archivo CSV
    with open(ruta_stats, mode='a', newline='') as file:
        writer = csv.writer(file)
        
        # Escribir encabezados si el archivo está vacío
        if file.tell() == 0:
            writer.writerow([
                'ID', 'Tipo', 'Energía Consumida (J)'
            ])
        
        # Escribir las estadísticas de cada CH y nodo en el archivo
        for key, value in stats["stats_proTx"].items():
            writer.writerow([
                # method_name,
                key, 
                "CH" if "CH" in key else "Nodo",
                value.get("energy_consumed", ''),
                # value.get("sync_time", ''),
                # value.get("retransmissions", ''),
                # value.get("is_syn", '')
            ])

    print(f"Estadísticas guardadas en: {ruta_stats}")



def save_stats_to_csv(stats, filename):
    """Guarda las estadísticas en un archivo CSV"""
    import csv
    
    # Obtener la ruta actual y definir la carpeta 'stats' para guardar el archivo
    current_dir = os.getcwd()
    files_stats = os.path.join(current_dir, 'stats')
    
    # Crear la carpeta si no existe
    if not os.path.exists(files_stats):
        os.makedirs(files_stats)

    # Ruta completa del archivo dentro de la carpeta 'stats'
    ruta_stats = os.path.join(files_stats, filename)

    # Preparar datos para CSV
    id_ch = stats["energy"]["CH"]["id"]
    energy_ch_tx = stats["energy"]["CH"]["tx"]
    energy_ch_rx = stats["energy"]["CH"]["rx"]
    id_sn = stats["energy"]["SN"]["id"]
    energy_sn_tx = stats["energy"]["SN"]["tx"]
    energy_sn_rx = stats["energy"]["SN"]["rx"]
    times_prop = stats["times"]["propagation"]
    times_prop_all = stats["times"]["propagation_all"]
    times_verif = stats["times"]["verification"]
    times_response = stats["times"]["response"]
    attempts = stats["attempts"]
    
    # Escribir archivo CSV
    with open(ruta_stats, 'w', newline='') as csvfile:
        writer = csv.writer(csvfile)
        
        # Encabezados
        writer.writerow([
            "Tipo", "Id_CH", "Energía CH Tx", "Energía CH Rx", 
            "Id_SN", "Energía SN Tx", "Energía SN Rx",
            "Tiempo Propagación", "Tiempo Propagación all", 
            "Tiempo Verificación", "Tiempo de respuesta auth"
        ])
        
        # Datos (una fila por cada medición)
        max_len = max(
            len(id_ch),
            len(energy_ch_tx), len(energy_ch_rx),
            len(id_sn),
            len(energy_sn_tx), len(energy_sn_rx),
            len(times_prop), len(times_prop_all),
            len(times_verif), len(times_response)
        )
        
        for i in range(max_len):
            writer.writerow([
                f"Medición {i+1}",
                id_ch[i] if i < len(id_ch) else "",
                energy_ch_tx[i] if i < len(energy_ch_tx) else "",
                energy_ch_rx[i] if i < len(energy_ch_rx) else "",
                id_sn[i] if i < len(id_sn) else "",
                energy_sn_tx[i] if i < len(energy_sn_tx) else "",
                energy_sn_rx[i] if i < len(energy_sn_rx) else "",
                times_prop[i] if i < len(times_prop) else "",
                times_prop_all[i] if i < len(times_prop_all) else "",
                times_verif[i] if i < len(times_verif) else "",
                times_response[i] if i < len(times_response) else ""
            ])
        
        # Totales
        writer.writerow([
            "TOTALES","",
            sum(energy_ch_tx),
            sum(energy_ch_rx),
            "",
            sum(energy_sn_tx),
            sum(energy_sn_rx),
            sum(times_prop),
            sum(times_prop_all),
            sum(times_verif),
            sum(times_response)
        ])

        writer.writerow([
            "attempts", attempts,
        ])
    
    print(f"Estadísticas guardadas en {filename}")
