from setuptools import setup
from Cython.Build import cythonize

# lista de los modulos a compilar
source_files = [
    "a_run_many.py",
    "bbdd2_sqlite3.py",
    "cluster.py",
    "create_nodes_light.py",
    "curva_anclada_distancias_menores.py",
    "energia_dinamica.py",
    "noise_uan_aariza.py",
    "path_loss.py",
    "per_from_link_uan.py",
    "propagacionTx_light.py",
    "simulation_test1_light.py",
    "syn_light.py",
    "tangle_logger_light.py",
    "tangle2_light.py",
    "temperature_models_uan.py",
    "transmission_logger_uan.py",
    "transmission_summary_uan.py",
    "transmit_data_light_uan.py"
]

setup(
    ext_modules=cythonize(
        source_files,
        compiler_directives={"language_level":"3"}
    ),
    script_args=["build_ext", "--inplace"]
)