import os
import sys
from pathlib import Path
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler

sys.path.append(os.path.dirname(__file__))
from log_parser import parse_logs
from feature_extractor import extract_features
from anomaly_detector import FEATURES

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
