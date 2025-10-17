import pickle
import os
import json

# Obtener la ruta del directorio donde se encuentra el script actual
# current_dir = os.path.dirname(os.path.abspath(__file__))
current_dir = os.getcwd()

# Definir la carpeta donde se encuentra la base de datos (carpeta 'save_struct')
carpeta_destino = os.path.join(current_dir, 'save_struct')

# Ruta completa del archivo de la base de datos dentro de la carpeta 'save_struct'
ruta_nodos = os.path.join(carpeta_destino, 'nodos_guardados.pkl')
ruta_sink = os.path.join(carpeta_destino, 'sink_guardado.pkl')

# Cargas nodos y sink
# Para cargar la estructura de nodos guardada
with open(ruta_nodos, 'rb') as file:
    node_uw = pickle.load(file)

# Para cargar la estructura de nodos guardada
with open(ruta_sink, 'rb') as file:
    nodo_sink = pickle.load(file)


# Función para convertir objetos complejos a JSON de forma legible
def convert_to_json(data):
    def default_converter(o):
        if isinstance(o, bytes):
            return o.decode('utf-8', 'ignore')  # Convertir bytes a string
        if hasattr(o, '__dict__'):
            return o.__dict__  # Convertir objetos a diccionarios si tienen atributos
        return str(o)  # Convertir a string como última opción

    return json.dumps(data, default=default_converter, indent=4)

# Convertir las estructuras a JSON
json_sink = convert_to_json(nodo_sink)
json_nodes = convert_to_json(node_uw)

# print('SINK')
# # print(nodo_sink)
# print(json_sink)
# print('NODES DESPLEGADOS')
# # print(node_uw)
# print(json_nodes)


# Opcional: guardar las estructuras JSON en archivos para su uso posterior
with open(os.path.join(carpeta_destino, 'sink_guardado.json'), 'w') as sink_file:
    sink_file.write(json_sink)

with open(os.path.join(carpeta_destino, 'nodos_guardados.json'), 'w') as nodes_file:
    nodes_file.write(json_nodes)

# nodo_sink['RegisterNodes'][1]['Status_auth'] = True

# print(nodo_sink['RegisterNodes'][10]['Status_auth'])

# print(nodo_sink)
# print(node_uw[14])
# print(node_uw[1])

# import numpy as np
# # dist = np.linalg.norm(node_uw[5]["Position"] - node_uw[2]["Position"])  # Distancia entre el nodo y el objetivo
# dist = np.linalg.norm(node_uw[17]["Position"] - nodo_sink["Position"])  # Distancia entre el nodo y el objetivo
# print("Distancia entre el sink y ch : ", dist)

# dist = np.linalg.norm(node_uw[21]["Position"] - nodo_sink["Position"])  # Distancia entre el nodo y el objetivo
# print("Distancia entre el sink y ch : ", dist)

# dist = np.linalg.norm(node_uw[22]["Position"] - nodo_sink["Position"])  # Distancia entre el nodo y el objetivo
# print("Distancia entre el sink y ch : ", dist)

# dist = np.linalg.norm(node_uw[24]["Position"] - nodo_sink["Position"])  # Distancia entre el nodo y el objetivo
# print("Distancia entre el sink y ch : ", dist)

# dist = np.linalg.norm(node_uw[26]["Position"] - nodo_sink["Position"])  # Distancia entre el nodo y el objetivo
# print("Distancia entre el sink y ch : ", dist)