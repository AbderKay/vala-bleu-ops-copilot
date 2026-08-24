import joblib
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, confusion_matrix
from sentence_transformers import SentenceTransformer
from sklearn.model_selection import cross_val_score

EMBED_MODEL = "intfloat/multilingual-e5-small"
MODEL_PATH = "backend/app/router/router_clf.joblib"

# --- Fonction appelable par l'API (charge le modèle une seule fois) ---
_clf = None
_embed = None


def route(question):
    """Charge le classifieur sauvegardé et prédit l'intention d'une question."""
    global _clf, _embed
    if _clf is None:
        _clf = joblib.load(MODEL_PATH)["clf"]
        _embed = SentenceTransformer(EMBED_MODEL)
    emb = _embed.encode([f"query: {question}"], normalize_embeddings=True)
    return _clf.predict(emb)[0]


TRAIN = [
    # RAG (connaissance / doc)
    ("Comment créer une adresse email professionnelle ?", "RAG"),
    ("Comment installer WordPress sur mon hébergement ?", "RAG"),
    ("Comment configurer un enregistrement A ?", "RAG"),
    ("Comment activer le SSL sur mon domaine ?", "RAG"),
    ("Comment transférer mon nom de domaine ?", "RAG"),
    ("Comment créer une base de données MySQL ?", "RAG"),
    ("Comment se connecter en FTP ?", "RAG"),
    ("Quels sont les plans d'hébergement disponibles ?", "RAG"),
    ("Comment vider le cache du CDN ?", "RAG"),
    ("Comment renouveler mon abonnement ?", "RAG"),
    ("Comment configurer les DNS de mon domaine ?", "RAG"),
    ("Comment ajouter un contact de facturation ?", "RAG"),
    ("Comment restaurer une sauvegarde de mon site ?", "RAG"),
    ("Comment créer un compte de messagerie ?", "RAG"),
    ("Comment pointer mon domaine vers l'hébergement ?", "RAG"),
    # LOGS (état système / sécurité)
    ("Y a-t-il une anomalie de trafic sur srv-42 ?", "LOGS"),
    ("Quelles adresses IP sont suspectes aujourd'hui ?", "LOGS"),
    ("Détecte-t-on une attaque par force brute ?", "LOGS"),
    ("Y a-t-il un pic d'erreurs 500 récemment ?", "LOGS"),
    ("Combien de requêtes 404 sur la dernière heure ?", "LOGS"),
    ("Y a-t-il eu un scan de ports sur le serveur ?", "LOGS"),
    ("Quel est le taux d'erreur du serveur mutualisé ?", "LOGS"),
    ("Montre les IP avec un comportement anormal", "LOGS"),
    ("Des tentatives d'intrusion ont-elles été détectées ?", "LOGS"),
    ("Analyse le trafic HTTP des dernières 24h", "LOGS"),
    ("Y a-t-il une surcharge de trafic anormale ?", "LOGS"),
    ("Quelles IP génèrent le plus d'erreurs ?", "LOGS"),
    ("Signale les pics de charge du serveur", "LOGS"),
    ("Y a-t-il des connexions anormales en ce moment ?", "LOGS"),
    ("Le serveur subit-il une attaque DDoS ?", "LOGS"),
    # MIXTE (connaissance + état système)
    ("Explique la config MX et vérifie s'il y a une anomalie mail", "MIXTE"),
    ("Comment sécuriser SSH et y a-t-il des scans en cours ?", "MIXTE"),
    ("Documente le SSL et dis-moi s'il y a des erreurs HTTPS", "MIXTE"),
    ("Comment configurer le CDN et y a-t-il un pic de trafic ?", "MIXTE"),
    ("Procédure de sauvegarde et état actuel des serveurs ?", "MIXTE"),
    ("Explique le DNS et détecte les IP suspectes", "MIXTE"),
    ("Comment installer WordPress et y a-t-il des tentatives de piratage ?", "MIXTE"),
    ("Rappelle la config FTP et vérifie les connexions anormales", "MIXTE"),
    ("Comment créer une base MySQL et y a-t-il une surcharge serveur ?", "MIXTE"),
    ("Guide du pare-feu et détecte les attaques récentes", "MIXTE"),
    ("Comment activer le SSL et signale les erreurs 500", "MIXTE"),
    ("Comment configurer les emails et y a-t-il un pic de spam ?", "MIXTE"),
    ("Comment protéger mon site et quelles IP sont suspectes ?", "MIXTE"),
    ("Config DNS et anomalies de trafic des dernières 24h ?", "MIXTE"),
    ("Explique le transfert de domaine et l'état actuel du trafic", "MIXTE"),
]

TEST = [
    ("Comment configurer un enregistrement MX ?", "RAG"),
    ("Comment activer un certificat SSL ?", "RAG"),
    ("Comment changer le mot de passe FTP ?", "RAG"),
    ("Quels sont vos tarifs d'hébergement ?", "RAG"),
    ("Y a-t-il une anomalie de trafic ces dernières 24h ?", "LOGS"),
    ("Quelles IP suspectes ont accédé au serveur ?", "LOGS"),
    ("Détecte-t-on une tentative de brute-force ?", "LOGS"),
    ("Y a-t-il un pic d'erreurs 500 sur le serveur ?", "LOGS"),
    ("Explique la config DNS et vérifie s'il y a une anomalie de trafic", "MIXTE"),
    ("Comment sécuriser le SSH et y a-t-il des scans en cours ?", "MIXTE"),
]


def embed(model, texts):
    return model.encode([f"query: {t}" for t in texts], normalize_embeddings=True)


def main():
    model = SentenceTransformer(EMBED_MODEL)
    Xtr = embed(model, [q for q, _ in TRAIN]); ytr = [l for _, l in TRAIN]
    Xte = embed(model, [q for q, _ in TEST]); yte = [l for _, l in TEST]

    clf = LogisticRegression(max_iter=1000, class_weight="balanced")
    clf.fit(Xtr, ytr)
    pred = list(clf.predict(Xte))

    for (q, attendu), p in zip(TEST, pred):
        ok = "✅" if p == attendu else "❌"
        print(f"{ok} [attendu {attendu:5s} → prédit {p:5s}] {q}")

    acc = accuracy_score(yte, pred)
    labels = ["RAG", "LOGS", "MIXTE"]
    cm = confusion_matrix(yte, pred, labels=labels)
    print(f"\n🎯 Précision (Approche B) : {acc:.0%}  [cible ≥ 90%]")
    print("\nMatrice de confusion (lignes = vérité, colonnes = prédit)")
    print("        " + "  ".join(f"{l:5s}" for l in labels))
    for l, row in zip(labels, cm):
        print(f"{l:6s}  " + "  ".join(f"{v:5d}" for v in row))
        # Validation croisée : métrique bien plus honnête qu'un test unique
    allX = embed(model, [q for q, _ in TRAIN + TEST])
    ally = [l for _, l in TRAIN + TEST]
    cv = cross_val_score(
        LogisticRegression(max_iter=1000, class_weight="balanced"),
        allX, ally, cv=5
    )
    print(f"\n🔬 Validation croisée 5-fold : {cv.mean():.0%} ± {cv.std():.0%}")
    joblib.dump({"clf": clf, "labels": labels}, MODEL_PATH)
    print(f"\n✅ Classifieur sauvegardé : {MODEL_PATH}")


if __name__ == "__main__":
    main()