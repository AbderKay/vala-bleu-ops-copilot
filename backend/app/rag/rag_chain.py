#tout est dans anaconda prompt .

import os
import sys
import ollama

# permet d'importer retriever.py peu importe d'où on lance le script
sys.path.append(os.path.dirname(__file__))
from retriever import retrieve

LLM_MODEL = "qwen2.5:1.5b"   # petit modèle CPU — deviendra "qwen2.5:7b" sur GPU

SYSTEM_PROMPT = """Tu es l'assistant technique de Vala Bleu (hébergeur web).
Réponds à la question en te basant UNIQUEMENT sur le CONTEXTE fourni.
Si le contexte ne contient pas la réponse, dis-le clairement — n'invente rien.
Termine toujours par la source sous la forme [Source: titre]."""

# --- Détection de langue (multilingue FR / EN / AR) ---
try:
    from langdetect import detect
except ImportError:
    detect = None

LANG_NAMES = {"fr": "français", "en": "English", "ar": "l'arabe (العربية)"}


def detect_lang(text):
    """Détecte la langue de la question (fr / en / ar), défaut fr."""
    if detect is None:
        return "fr"
    try:
        code = detect(text)
    except Exception:
        code = "fr"
    return code if code in ("fr", "en", "ar") else "fr"


def build_context(chunks):
    """Assemble les passages en un bloc de contexte lisible par le LLM."""
    blocs = [f"[Source: {c['titre']}]\n{c['content']}" for c in chunks]
    return "\n\n---\n\n".join(blocs)


def answer(question):
    # 0) Détecter la langue de la question -> répondre dans cette langue
    lang = detect_lang(question)
    consigne = f"\nIMPORTANT : réponds IMPÉRATIVEMENT en {LANG_NAMES[lang]}."
    # 1) Retrieval : trouver les passages pertinents (l'e5 est cross-lingue)
    chunks = retrieve(to_french(question, lang))    
    # 2) Augmentation : construire le prompt avec le contexte
    contexte = build_context(chunks)
    user_prompt = f"CONTEXTE :\n{contexte}\n\nQUESTION : {question}"
    # 3) Generation : demander la réponse au LLM local
    reponse = ollama.chat(
        model=LLM_MODEL,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT + consigne},
            {"role": "user", "content": user_prompt},
        ],
    )
    return reponse["message"]["content"], chunks

SMALLTALK_PROMPT = """Tu es l'assistant virtuel de Vala Bleu (hébergeur web), sympathique et professionnel.
Réponds brièvement et naturellement aux messages de conversation (salutations, remerciements, "qui es-tu", etc.).
Si le message est hors de ton domaine, réponds poliment puis rappelle que tu peux aider sur l'hébergement
(SSL, DNS, email, MySQL, noms de domaine) et sur l'état des serveurs (anomalies de trafic).
Reste toujours dans ton rôle. Réponds dans la langue du message."""


def smalltalk(question):
    """Réponse conversationnelle (hors RAG/Logs) pour les messages hors-sujet."""
    lang = detect_lang(question)
    resp = ollama.chat(
        model=LLM_MODEL,
        messages=[
            {"role": "system", "content": SMALLTALK_PROMPT + f"\nRéponds en {LANG_NAMES[lang]}."},
            {"role": "user", "content": question},
        ],
    )
    return resp["message"]["content"]
def to_french(question, lang):
    """Traduit la question en français pour un retrieval cohérent entre langues."""
    if lang == "fr":
        return question
    resp = ollama.chat(
        model=LLM_MODEL,
        messages=[
            {"role": "system", "content": "Traduis en français. Réponds UNIQUEMENT par la traduction, sans rien ajouter."},
            {"role": "user", "content": question},
        ],
    )
    return resp["message"]["content"].strip()


SMALLTALK_PROMPT = """Tu es l'assistant virtuel de Vala Bleu (hébergeur web), sympathique et professionnel.
Réponds brièvement et naturellement aux messages de conversation (salutations, remerciements, "qui es-tu", etc.).
Si le message est hors de ton domaine, réponds poliment puis rappelle que tu peux aider sur l'hébergement
(SSL, DNS, email, MySQL, noms de domaine) et sur l'état des serveurs (anomalies de trafic).
Reste toujours dans ton rôle. Réponds dans la langue du message."""


def smalltalk(question):
    """Réponse conversationnelle (hors RAG/Logs) pour les messages hors-sujet."""
    lang = detect_lang(question)
    resp = ollama.chat(
        model=LLM_MODEL,
        messages=[
            {"role": "system", "content": SMALLTALK_PROMPT + f"\nRéponds en {LANG_NAMES[lang]}."},
            {"role": "user", "content": question},
        ],
    )
    return resp["message"]["content"]


if __name__ == "__main__":
    q = "Comment générer un certificat SSL chez Vala Bleu ?"
    print(f"❓ {q}\n⏳ (génération sur CPU, sois patient...)\n")
    reponse, sources = answer(q)
    print("🤖 Réponse :\n", reponse)
    print("\n📚 Sources récupérées :")
    for s in sources:
        print(f"  - {s['titre']} [{s['source_url']}]")