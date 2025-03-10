import shutil
import os

def replicate_database_for_nodes(original_db, num_nodes):
    """Replica la base de datos existente para cada nodo en la red."""
    if not os.path.exists("nodes_db"):
        os.makedirs("nodes_db")

    for node_id in range(1, num_nodes + 1):
        node_db_path = f"nodes_db/node_{node_id}.db"
        shutil.copyfile(original_db, node_db_path)
        print(f"📂 Base de datos replicada para nodo {node_id} en {node_db_path}")

# 📌 Llamada para replicar la BBDD en 20 nodos
replicate_database_for_nodes("data/bbdd_keys_shared_sign_cipher.db", num_nodes=20)
