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
            writer.writerow(['Times CreateTxGen', 'Times VerifyTx', 'Times TxResponse'])

        # Convertir las estadísticas en filas y escribirlas en el archivo
        for i in range(len(stats_tx['times_createTxgen'])):
            writer.writerow([
                stats_tx['times_createTxgen'][i],
                stats_tx['times_verifyTx'][i] if i < len(stats_tx['times_verifyTx']) else '',
                stats_tx['times_Txresponse'][i] if i < len(stats_tx['times_Txresponse']) else ''
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