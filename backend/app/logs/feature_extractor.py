import os
import sys
import pandas as pd

sys.path.append(os.path.dirname(__file__))
from log_parser import parse_logs


def extract_features(df):
    """Résume le comportement de chaque IP en features numériques."""
    df = df.copy()
    df["size"] = pd.to_numeric(df["size"], errors="coerce").fillna(0)
    df["is_error"] = df["status"] >= 400          # 4xx et 5xx = erreurs

    g = df.groupby("ip")
    feats = pd.DataFrame({
        "n_requests":     g.size(),
        "error_rate":     g["is_error"].mean(),
        "n_unique_paths": g["path"].nunique(),
        "n_unique_ua":    g["ua"].nunique(),
        "avg_size":       g["size"].mean(),
    })

    # requêtes par minute (volume / durée d'activité de l'IP)
    span_min = g["time"].apply(
        lambda s: max((s.max() - s.min()).total_seconds() / 60, 1)
    )
    feats["req_per_min"] = feats["n_requests"] / span_min

    return feats.reset_index()


if __name__ == "__main__":
    df = parse_logs()
    feats = extract_features(df)
    print(feats.head(10), "\n")
    print(f"✅ Features calculées pour {len(feats)} IP.\n")
    print("Statistiques (pour repérer les valeurs extrêmes) :")
    print(feats.describe())