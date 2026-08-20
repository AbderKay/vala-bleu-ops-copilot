import os
import sys
import joblib
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler

sys.path.append(os.path.dirname(__file__))
from log_parser import parse_logs
from feature_extractor import extract_features

FEATURES = ["n_requests", "error_rate", "n_unique_paths",
            "n_unique_ua", "avg_size", "req_per_min"]
MODEL_PATH = "backend/app/logs/iforest.joblib"


def train_and_score(feats, contamination=0.05):
    X = feats[FEATURES].values
    scaler = StandardScaler()
    Xs = scaler.fit_transform(X)                    # normalisation

    model = IsolationForest(
        n_estimators=200, contamination=contamination, random_state=42
    )
    model.fit(Xs)

    feats = feats.copy()
    feats["anomaly_score"] = model.decision_function(Xs)   # haut=normal, bas=anormal
    feats["is_anomaly"] = model.predict(Xs) == -1          # -1 => anomalie

    joblib.dump({"model": model, "scaler": scaler, "features": FEATURES}, MODEL_PATH)
    return feats


if __name__ == "__main__":
    df = parse_logs()
    feats = extract_features(df)
    scored = train_and_score(feats)

    print("Les 10 IP les plus 'anormales' (score le plus bas) :")
    cols = ["ip", "n_requests", "error_rate", "n_unique_paths", "anomaly_score", "is_anomaly"]
    print(scored.sort_values("anomaly_score").head(10)[cols].to_string(index=False))

    print(f"\n✅ Modèle entraîné et sauvegardé : {MODEL_PATH}")
    print(f"Anomalies flaguées : {scored['is_anomaly'].sum()} / {len(scored)} IP")