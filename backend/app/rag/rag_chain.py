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
Termine toujours par la source sous la forme [Source: titre].
Réponds en français, clair et concis."""


def build_context(chunks):
    """Assemble les passages en un bloc de contexte lisible par le LLM."""
    blocs = [f"[Source: {c['titre']}]\n{c['content']}" for c in chunks]
    return "\n\n---\n\n".join(blocs)


def answer(question):
    # 1) Retrieval : trouver les passages pertinents
    chunks = retrieve(question)
    # 2) Augmentation : construire le prompt avec le contexte
    contexte = build_context(chunks)
    user_prompt = f"CONTEXTE :\n{contexte}\n\nQUESTION : {question}"
    # 3) Generation : demander la réponse au LLM local
    reponse = ollama.chat(
        model=LLM_MODEL,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ],
    )
    return reponse["message"]["content"], chunks


if __name__ == "__main__":
    q = "Comment générer un certificat SSL chez Vala Bleu ?"
    print(f"❓ {q}\n⏳ (génération sur CPU, sois patient...)\n")
    reponse, sources = answer(q)
    print("🤖 Réponse :\n", reponse)
    print("\n📚 Sources récupérées :")
    for s in sources:
        print(f"  - {s['titre']} [{s['source_url']}]")