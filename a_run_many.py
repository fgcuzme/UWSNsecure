# run_many.py
import os, subprocess

def run_batch(
    scenario="1000km_W5_Sh0.5",
    runs=5,
    seed0=1337,
    num_nodes=20,
    seeds_mode="inc"   # "inc" => seed0, seed0+1,...  | "same" => mismo seed para todos
):
    env_base = os.environ.copy()
    env_base["SCENARIO_ID"] = scenario

    for i in range(1, runs+1):
        env = env_base.copy()
        env["RUN"] = str(i)
        env["UWSN_SEED"] = str(seed0 if seeds_mode=="same" else (seed0 + i - 1))
        env["NUM_NODES"] = str(num_nodes)
        print(f"\n>>> RUN={env['RUN']} SEED={env['UWSN_SEED']}")
        # knobs de rendimiento/registro (ver sección 4)
        # env.setdefault("UWSN_TANGLE_SAMPLING", "1.0")   # mide todo (o 0.25 para 25%)
        # env.setdefault("UWSN_TANGLE_BATCH", "64")       # flush CSV cada 64 eventos
        # env.setdefault("UWSN_TANGLE_RESERVOIR", "1024") # p* cálculos
        # ejecuta la simulación
        subprocess.run(["python", "simulation_test1_light.py"], env=env, check=True)

if __name__ == "__main__":
    run_batch(scenario=os.environ.get("SCENARIO_ID","1000km_W5_Sh0.5"),
              runs=int(os.environ.get("RUNS","10")),
              seed0=int(os.environ.get("SEED0","1337")),
              num_nodes=int(os.environ.get("NUM_NODES", "20")),
              seeds_mode=os.environ.get("SEEDS_MODE","inc"))
