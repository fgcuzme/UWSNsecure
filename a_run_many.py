# run_many.py
import os, subprocess

# node_sizes = [20, 50, 100, 200, 300, 400, 500]
# node_sizes = [400, 500, 700, 900, 1000]
node_sizes = [20]

def run_batch(
    scenario="1000km_W5_Sh0.5",
    runs=5,
    seed0=1337,
    seeds_mode="inc"   # "inc" => seed0, seed0+1,...  | "same" => mismo seed para todos
):
    env_base = os.environ.copy()
    env_base["SCENARIO_ID"] = scenario

    for size in node_sizes:    
        for i in range(1, runs+1):
            env = env_base.copy()
            env["RUN"] = str(i)
            env["UWSN_SEED"] = str(seed0 if seeds_mode=="same" else (seed0 + i - 1))
            env["UNSN_NUM_NODES"] = str(size)  # 👈 nuevo parámetro
            run_dir = f"results/nodes_{size}/run_{i}"
            env["OUTPUT_DIR"] = run_dir
            env["PER_VARIABLE"] = "None"  # 👈 aquí defines la variable de entorno "None" or "0.15"

            print(f">>> NODES={size} RUN={env['RUN']} SEED={env['UWSN_SEED']}")
            # knobs de rendimiento/registro (ver sección 4)
            # env.setdefault("UWSN_TANGLE_SAMPLING", "1.0")   # mide todo (o 0.25 para 25%)
            # env.setdefault("UWSN_TANGLE_BATCH", "64")       # flush CSV cada 64 eventos
            # env.setdefault("UWSN_TANGLE_RESERVOIR", "1024") # p* cálculos
            # ejecuta la simulación
            subprocess.run(["python", "simulation_test1_light.py",
                            "--output_dir", run_dir], env=env, check=True)
            # subprocess.run(["./simulation_test1_light_arm",
            #                 "--output_dir", run_dir], env=env, check=True)

if __name__ == "__main__":
    run_batch(scenario=os.environ.get("SCENARIO_ID","1000km_W5_Sh0.5"),
              runs=int(os.environ.get("RUNS","1")),
              seed0=int(os.environ.get("SEED0","1337")),
              #num_nodes=int(os.environ.get("NUM_NODES", "20")),
              seeds_mode=os.environ.get("SEEDS_MODE","inc"))
