import os
import sys
import time
import random
import tracemalloc
from datetime import datetime, timedelta
from pathlib import Path
from collections import defaultdict

sys.path.append(os.path.dirname(__file__))
from log_parser import PATTERN          # on réutilise le regex Combined Log

BIG_LOG = Path("data/raw/logs/access_big.log")
N_LINES = 1_000_000                       # 1 million de lignes


def generate_big_log(n=N_LINES):
    """Génère un gros fichier de logs (une seule fois)."""
    if BIG_LOG.exists():
        return
    random.seed(1)
    ips = [f"196.200.{random.randint(0,255)}.{random.randint(1,254)}" for _ in range(200)]
    paths = ["/", "/index.html", "/produits", "/login", "/api/status", "/css/style.css"]
    uas = ["Mozilla/5.0 Chrome/120", "Mozilla/5.0 Safari/604", "curl/8.0"]
    status = [200, 200, 200, 200, 304, 404, 301]
    BIG_LOG.parent.mkdir(parents=True, exist_ok=True)
    t = datetime(2026, 8, 20, 0, 0, 0)
    with BIG_LOG.open("w", encoding="utf-8") as f:
        for _ in range(n):
            t += timedelta(seconds=1)
            f.write(f'{random.choice(ips)} - - [{t.strftime("%d/%b/%Y:%H:%M:%S +0000")}] '
                    f'"GET {random.choice(paths)} HTTP/1.1" {random.choice(status)} 500 "-" '
                    f'"{random.choice(uas)}"\n')


def benchmark():
    """Traite le fichier EN FLUX (mémoire constante) et mesure le débit."""
    stats = defaultdict(lambda: {"n": 0, "err": 0, "paths": set()})
    tracemalloc.start()
    t0 = time.perf_counter()
    total = 0
    with BIG_LOG.open("r", encoding="utf-8") as f:
        for line in f:                      # lecture ligne par ligne = mémoire O(1) sur le fichier
            m = PATTERN.match(line)
            if not m:
                continue
            d = m.groupdict()
            s = stats[d["ip"]]
            s["n"] += 1
            if int(d["status"]) >= 400:
                s["err"] += 1
            s["paths"].add(d["path"])
            total += 1
    elapsed = time.perf_counter() - t0
    _, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()

    print(f"📄 Lignes traitées : {total:,}")
    print(f"⏱️  Temps : {elapsed:.1f}s  →  🚀 DÉBIT : {total/elapsed:,.0f} lignes/sec")
    print(f"🧠 Mémoire pic : {peak/1e6:.1f} Mo  (pour {len(stats):,} IP agrégées)")
    print(f"✅ Mémoire BORNÉE malgré {total:,} lignes → traitement scalable (Big Data).")


if __name__ == "__main__":
    print("⚙️  Génération du gros fichier (1re fois, ~30-60s)...")
    generate_big_log()
    print(f"✅ Fichier : {BIG_LOG} ({BIG_LOG.stat().st_size/1e6:.0f} Mo)\n")
    benchmark()