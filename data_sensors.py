import random
import time
from datetime import datetime

def generate_sensor_data(node_id):
    """Genera datos simulados de un sensor submarino"""
    sensor_data = {
        "sensor_id": node_id,
        # "timestamp": datetime.utcnow().isoformat(),
        "temperature": round(random.uniform(2, 30), 2),
        # "salinity": round(random.uniform(30, 40), 2),
        # "ph": round(random.uniform(7.5, 8.5), 2),
        # "oxygen": round(random.uniform(6, 10), 2),
        # "pressure": round(random.uniform(1, 5), 2),
        # "current_speed": round(random.uniform(0.1, 2.5), 2),
        # "current_direction": random.randint(0, 360)
    }
    return sensor_data

# # Simulación de 10 mensajes de sensores
# for i in range(10):
#     data = generate_sensor_data(f"node_{i+1}")
#     print(data)
#     time.sleep(1)  # Simula retraso en la transmisión

