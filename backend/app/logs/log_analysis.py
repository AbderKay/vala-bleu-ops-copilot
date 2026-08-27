import os
import sys
from pathlib import Path
from collections import defaultdict
import numpy as np
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler

sys.path.append(os.path.dirname(__file__))
from log_parser import parse_logs, PATTERN
from feature_extractor import extract_features
from anomaly_detector import FEATURES

STREAM_LOG = Path("data/raw/logs/access_stream.log")


def analyze_stream(window=2000, contamination=0.1):
    """Couche SPEED : analyse la fenêtre récente du flux de logs en temps réel."""
    if not STREAM_LOG.exists():
        return {"total_ips": 0, "n_anomalies": 0, "anomalies": [], "window_lines": 0}
    lines = STREAM_LOG.read_text(encoding="utf-8").splitlines()[-window:]
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
    if len(ips) < 5:
        return {"total_ips": len(ips), "n_anomalies": 0, "anomalies": [], "window_lines": len(lines)}
    X = np.array([[s["n"], s["err"] / max(s["n"], 1), len(s["paths"])]
                  for s in stats.values()], dtype=float)
    Xs = StandardScaler().fit_transform(X)
    pred = IsolationForest(contamination=contamination, random_state=42).fit_predict(Xs)
    anomalies = [
        {"ip": ips[i], "n_requests": int(X[i][0]),
         "error_rate": round(float(X[i][1]), 3), "n_unique_paths": int(X[i][2])}
        for i in range(len(ips)) if pred[i] == -1
    ]
    anomalies.sort(key=lambda a: a["n_requests"], reverse=True)
    return {"total_ips": len(ips), "n_anomalies": len(anomalies),
            "anomalies": anomalies, "window_lines": len(lines)}

# par défaut on analyse le log avec attaques (pour une démo parlante)
DEFAULT_LOG = Path("data/raw/logs/access_eval.log")


def analyze_logs(log_path=DEFAULT_LOG, contamination=0.1):
    """Analyse un fichier de logs et renvoie les IP anormales détectées."""
    df = parse_logs(log_path)
    feats = extract_features(df)
    Xs = StandardScaler().fit_transform(feats[FEATURES].values)
    model = IsolationForest(n_estimators=200, contamination=contamination, random_state=42)
    feats = feats.copy()
    feats["is_anomaly"] = model.fit_predict(Xs) == -1
    anomalies = feats[feats["is_anomaly"]].sort_values("n_requests", ascending=False)
    return {
        "total_ips": int(len(feats)),
        "n_anomalies": int(feats["is_anomaly"].sum()),
        "anomalies": anomalies[["ip", "n_requests", "error_rate", "n_unique_paths"]]
                     .round(3).to_dict("records"),
    }


if __name__ == "__main__":
    import json
    print(json.dumps(analyze_logs(), indent=2, ensure_ascii=False))
