import os
import sys
import time
import numpy as np
from pathlib import Path
from collections import deque, defaultdict
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler

sys.path.append(os.path.dirname(__file__))
from log_parser import PATTERN

STREAM = Path("data/raw/logs/access_stream.log")
WINDOW = 2000      # fenêtre glissante (dernières lignes)
INTERVAL = 5       # analyse toutes les 5 secondes


def features_from_window(lines):
    stats = defaultdict(lambda: {"n": 0, "err": 0, "paths": set()})
    for l in lines:
        m = PATTERN.match(l)
        if not m:
            continue
        d = m.groupdict()
        s = stats[d["ip"]]
        s["n"] += 1
        if int(d["status"]) >= 400:
            s["err"] += 1
        s["paths"].add(d["path"])
    ips = list(stats.keys())
    X = np.array([[s["n"], s["err"] / max(s["n"], 1), len(s["paths"])]
                  for s in stats.values()], dtype=float)
    return ips, X


def main():
    STREAM.parent.mkdir(parents=True, exist_ok=True)
    STREAM.touch(exist_ok=True)
    window = deque(maxlen=WINDOW)
    pos = 0
    print(f"🌊 Consommateur (fenêtre {WINDOW} lignes, analyse /{INTERVAL}s). Ctrl+C pour arrêter.\n")
    while True:
        with STREAM.open("r", encoding="utf-8") as f:
            f.seek(pos)
            new = f.readlines()
            pos = f.tell()
        window.extend(new)
        if len(window) >= 50:
            ips, X = features_from_window(list(window))
            if len(ips) >= 5:
                Xs = StandardScaler().fit_transform(X)
                pred = IsolationForest(contamination=0.1, random_state=42).fit_predict(Xs)
                anomalies = [ips[i] for i in range(len(ips)) if pred[i] == -1]
                ts = time.strftime("%H:%M:%S")
                if anomalies:
                    print(f"[{ts}] ⚠️  {len(anomalies)} IP anormale(s) : {', '.join(anomalies[:5])}  ({len(window)} lignes)")
                else:
                    print(f"[{ts}] ✅ trafic normal ({len(window)} lignes, {len(ips)} IP)")
        time.sleep(INTERVAL)


if __name__ == "__main__":
    main()