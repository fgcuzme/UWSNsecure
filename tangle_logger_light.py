# 📁 tangle_logger_light.py — PERFILADO LIGERO PARA RPi
import os, csv, time, random, math
from collections import defaultdict

# === Configurables vía entorno ===
CSV_EVENTS = os.environ.get("UWSN_TANGLE_EVENTS", "stats/tangle_events_light.csv")
CSV_SUMMARY = os.environ.get("UWSN_TANGLE_SUMMARY", "stats/tangle_summary_light")
BATCH_SIZE = int(os.environ.get("UWSN_TANGLE_BATCH", "1"))         # flush cada N
SAMPLING_RATE = float(os.environ.get("UWSN_TANGLE_SAMPLING", "1.0")) # 1.0 => medir todo
RESERVOIR_K = int(os.environ.get("UWSN_TANGLE_RESERVOIR", "2048"))   # muestras p/percentiles
DISABLED = bool(int(os.environ.get("UWSN_TANGLE_OFF", "0")))         # 1 => no medir

# === Campos mínimos y estables (una fila por op medido) ===
FIELDS = [
    "ts_iso", "run_id", "phase", "module",
    "op", "node_id", "tx_id", "tx_type",
    "tips_before", "tips_after", "approved_count",
    # tiempos (ms)
    "t_sign", "t_verify", "t_canon", "t_hash",
    "t_tips_sel", "t_tips_store", "t_idx_upd",
    "t_nonce_chk", "t_ts_chk", "t_replay_chk",
    "t_other", "t_total",
    # tamaños
    "payload_bytes", "tx_bytes",
    # flags
    "sig_ok", "nonce_ok", "ts_ok", "replay_ok",
]

# --- Estado interno (buffer + resumen online) ---
_buf = []
_inited = False

def _ensure_dir(path):
    d = os.path.dirname(path)
    if d and not os.path.exists(d):
        os.makedirs(d, exist_ok=True)

def _init():
    global _inited
    if _inited: return
    _ensure_dir(CSV_EVENTS); _ensure_dir(CSV_SUMMARY)
    if not os.path.exists(CSV_EVENTS):
        with open(CSV_EVENTS, "w", newline="") as f:
            csv.DictWriter(f, fieldnames=FIELDS).writeheader()
    _inited = True

def _ts_iso():
    # UTC, sin dependencias extra
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())

# ===== Cronómetro ligero (ns -> ms) =====
class MsTimer:
    __slots__ = ("_t0_ns","ms")
    def __enter__(self):
        self._t0_ns = time.perf_counter_ns()
        return self
    def __exit__(self, et, ev, tb):
        self.ms = (time.perf_counter_ns() - self._t0_ns) / 1_000_000.0

# ===== Registro de eventos con muestreo =====
def log_tangle_event(
    *, run_id, phase, module, op,
    node_id, tx_id=None, tx_type=None,
    tips_before=None, tips_after=None, approved_count=None,
    t_sign=None, t_verify=None, t_canon=None, t_hash=None,
    t_tips_sel=None, t_tips_store=None, t_idx_upd=None,
    t_nonce_chk=None, t_ts_chk=None, t_replay_chk=None,
    t_other=None, t_total=None,
    payload_bytes=None, tx_bytes=None,
    sig_ok=None, nonce_ok=None, ts_ok=None, replay_ok=None,
):
    if DISABLED: 
        return
    if SAMPLING_RATE < 1.0 and random.random() > SAMPLING_RATE:
        return

    _init()
    row = {
        "ts_iso": _ts_iso(),
        "run_id": run_id, "phase": phase, "module": module,
        "op": op, "node_id": int(node_id) if node_id is not None else None,
        "tx_id": tx_id, "tx_type": tx_type,
        "tips_before": _int_or_none(tips_before),
        "tips_after": _int_or_none(tips_after),
        "approved_count": _int_or_none(approved_count),
        "t_sign": _f(t_sign), "t_verify": _f(t_verify),
        "t_canon": _f(t_canon), "t_hash": _f(t_hash),
        "t_tips_sel": _f(t_tips_sel), "t_tips_store": _f(t_tips_store),
        "t_idx_upd": _f(t_idx_upd),
        "t_nonce_chk": _f(t_nonce_chk), "t_ts_chk": _f(t_ts_chk), "t_replay_chk": _f(t_replay_chk),
        "t_other": _f(t_other), "t_total": _f(t_total),
        "payload_bytes": _int_or_none(payload_bytes),
        "tx_bytes": _int_or_none(tx_bytes),
        "sig_ok": _bool_or_none(sig_ok),
        "nonce_ok": _bool_or_none(nonce_ok),
        "ts_ok": _bool_or_none(ts_ok),
        "replay_ok": _bool_or_none(replay_ok),
    }
    _buf.append(row)
    if len(_buf) >= BATCH_SIZE:
        _flush_events()
    _update_summary(row)

def _f(x):
    try: return round(float(x), 4)
    except: return None

def _int_or_none(x):
    try: return int(x)
    except: return None

def _bool_or_none(x):
    if x is None: return None
    return bool(x)

def _flush_events():
    if not _buf: return
    with open(CSV_EVENTS, "a", newline="") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS)
        w.writerows(_buf)
    _buf.clear()

# ====== Agregado online por operación ======
# Welford para media/desv + reservoir para percentiles
class _Agg:
    __slots__ = ("n","mean","m2","min","max","res","res_n")
    def __init__(self):
        self.n = 0; self.mean = 0.0; self.m2 = 0.0; self.min = float("inf"); self.max = float("-inf")
        self.res = []         # reservoir
        self.res_n = 0        # elementos vistos para reservoir

    def add(self, x):
        # Welford
        self.n += 1
        delta = x - self.mean
        self.mean += delta / self.n
        self.m2 += delta * (x - self.mean)
        if x < self.min: self.min = x
        if x > self.max: self.max = x
        # Reservoir sampling (Vitter)
        self.res_n += 1
        if len(self.res) < RESERVOIR_K:
            self.res.append(x)
        else:
            j = random.randint(1, self.res_n)
            if j <= RESERVOIR_K:
                self.res[j-1] = x

    def stats(self):
        if self.n == 0:
            return {"n":0}
        var = self.m2 / (self.n - 1) if self.n > 1 else 0.0
        std = math.sqrt(max(0.0, var))
        samples = sorted(self.res) if self.res else []
        q = lambda p: _quantile(samples, p) if samples else None
        return {
            "n": self.n,
            "mean": self.mean,
            "std": std,
            "min": self.min, "max": self.max,
            "p50": q(0.50), "p90": q(0.90), "p95": q(0.95), "p99": q(0.99),
        }

def _quantile(sorted_samples, p):
    if not sorted_samples: return None
    k = p * (len(sorted_samples)-1)
    f = math.floor(k); c = math.ceil(k)
    if f == c: return float(sorted_samples[int(k)])
    return float(sorted_samples[f] + (sorted_samples[c]-sorted_samples[f])*(k-f))

# Mapa: (op, metric) -> _Agg
_SUMMARY = defaultdict(_Agg)

# Métricas de tiempo que agregamos (elige las que más te interesan publicar)
_METRICS = ("t_sign","t_verify","t_canon","t_hash",
            "t_tips_sel","t_tips_store","t_idx_upd",
            "t_nonce_chk","t_ts_chk","t_replay_chk",
            "t_total")

def _update_summary(row):
    op = row["op"] or "unknown"
    for m in _METRICS:
        v = row.get(m)
        if v is not None:
            _SUMMARY[(op,m)].add(v)

def flush_all():
    """ Llamar al final de la simulación. """
    _flush_events()

    # Obtener el run_id desde variable de entorno o parámetro
    run_id = os.environ.get("RUN", "run01")  # puedes usar str(run_num) si lo tienes como entero

    # escribir resumen
    _ensure_dir(CSV_SUMMARY)

     # Ruta con nombre por run
    resumen_path = os.path.join(f"{CSV_SUMMARY}_run{run_id:02d}.csv")

    with open(resumen_path, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["op","metric","n","mean_ms","std_ms","var_ms","min_ms","p50_ms","p90_ms","p95_ms","p99_ms","max_ms"])
        for (op, m), agg in sorted(_SUMMARY.items()):
            s = agg.stats()
            if not s.get("n"): continue
            varianza = s["std"]**2 if s.get("std") is not None else None
            w.writerow([
                op, m, s["n"],
                _r(s["mean"]), _r(s["std"]), _r(varianza), _r(s["min"]),
                _r(s["p50"]), _r(s["p90"]), _r(s["p95"]), _r(s["p99"]),
                _r(s["max"])
            ])

def _r(x):
    return None if x is None else round(float(x), 4)
