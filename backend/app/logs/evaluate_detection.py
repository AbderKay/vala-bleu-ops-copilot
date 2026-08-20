import os
import sys
import random
from datetime import datetime, timedelta
from pathlib import Path
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler

sys.path.append(os.path.dirname(__file__))
from log_parser import parse_logs
from feature_extractor import extract_features
from anomaly_detector import FEATURES

LOG_NORMAL = Path("data/raw/logs/access.log")
LOG_EVAL = Path("data/raw/logs/access_eval.log")

BRUTE_IPS = ["45.13.66.201", "91.200.12.9"]        # brute-force
SCAN_IPS = ["185.220.101.5", "80.94.95.112"]       # scanners
MALICIOUS = set(BRUTE_IPS + SCAN_IPS)
UA_BOT = "python-requests/2.31"


def line(ip, ts, path, status):
    return (f'{ip} - - [{ts.strftime("%d/%b/%Y:%H:%M:%S +0000")}] '
            f'"GET {path} HTTP/1.1" {status} 300 "-" "{UA_BOT}"')


def build_eval_log():
    base = LOG_NORMAL.read_text(encoding="utf-8").splitlines()
    extra = []
    t = datetime(2026, 8, 20, 12, 0, 0)
    # brute-force : marteler /login, erreurs 401
    for ip in BRUTE_IPS:
        for _ in range(300):
            t += timedelta(seconds=1)
            extra.append(line(ip, t, "/login", 401))
    # scan : plein de chemins, erreurs 404
    for ip in SCAN_IPS:
        for i in range(200):
            t += timedelta(seconds=1)
            extra.append(line(ip, t, f"/admin{i}.php", 404))
    LOG_EVAL.write_text("\n".join(base + extra), encoding="utf-8")


def main():
    build_eval_log()
    df = parse_logs(LOG_EVAL)
    feats = extract_features(df)

    Xs = StandardScaler().fit_transform(feats[FEATURES].values)
    model = IsolationForest(n_estimators=200, contamination=0.1, random_state=42)
    feats = feats.copy()
    feats["is_anomaly"] = model.fit_predict(Xs) == -1
    feats["malveillante"] = feats["ip"].isin(MALICIOUS)

    # Métriques
    detected = feats[feats["malveillante"] & feats["is_anomaly"]]
    recall = len(detected) / len(MALICIOUS)
    normals = feats[~feats["malveillante"]]
    fp = int(normals["is_anomaly"].sum())
    fpr = fp / len(normals)

    print("IP malveillantes injectées :")
    cols = ["ip", "n_requests", "error_rate", "n_unique_paths", "is_anomaly"]
    print(feats[feats["malveillante"]][cols].to_string(index=False))
    print(f"\n🎯 Recall (détection)   : {recall:.0%}  ({len(detected)}/{len(MALICIOUS)})   [cible ≥ 85%]")
    print(f"⚠️  Faux positifs        : {fp}/{len(normals)}  (FPR {fpr:.1%})   [cible ≤ 10%]")


if __name__ == "__main__":
    main()