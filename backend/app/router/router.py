import os
import sys
import json
import ollama

LLM_MODEL = "qwen2.5:1.5b"   # deviendra qwen2.5:7b sur GPU (routage plus précis)

ROUTER_PROMPT = """Tu es un routeur d'intention pour un assistant d'hébergement web (Vala Bleu).
Classe la question dans UNE catégorie :
- "RAG"  : connaissance / documentation (comment faire, configuration, procédure, tarifs...).
- "LOGS" : état du système / trafic / anomalies / sécurité / erreurs serveur.
- "MIXTE": nécessite les deux à la fois.
Réponds UNIQUEMENT en JSON : {"intent": "RAG"} ou {"intent": "LOGS"} ou {"intent": "MIXTE"}."""


def route(question):
    resp = ollama.chat(
        model=LLM_MODEL,
        messages=[
            {"role": "system", "content": ROUTER_PROMPT},
            {"role": "user", "content": question},
        ],
        format="json",          # force une sortie JSON
    )
    try:
        intent = json.loads(resp["message"]["content"]).get("intent", "RAG")
    except Exception:
        intent = "RAG"
    return intent if intent in ("RAG", "LOGS", "MIXTE") else "RAG"


# Jeu de test annoté (pour mesurer la précision)
TEST_SET = [
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


if __name__ == "__main__":
    correct = 0
    for q, attendu in TEST_SET:
        pred = route(q)
        ok = "✅" if pred == attendu else "❌"
        correct += (pred == attendu)
        print(f"{ok} [attendu {attendu:5s} → prédit {pred:5s}] {q}")
    acc = correct / len(TEST_SET)
    print(f"\n🎯 Précision de routage : {acc:.0%} ({correct}/{len(TEST_SET)})  [cible ≥ 90%]")