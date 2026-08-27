import os
from dotenv import load_dotenv
import psycopg
from pgvector.psycopg import register_vector
from sentence_transformers import SentenceTransformer

load_dotenv(override=True)

EMBED_MODEL = "intfloat/multilingual-e5-small"
TOP_K = 4

DB = dict(
    host=os.environ.get("POSTGRES_HOST", "localhost").strip(),
    port=int(os.environ.get("POSTGRES_PORT", "5433").strip()),
    dbname=os.environ["POSTGRES_DB"].strip(),
    user=os.environ["POSTGRES_USER"].strip(),
    password=os.environ["POSTGRES_PASSWORD"].strip(),
)

# On charge le modèle une seule fois (coûteux à charger)
_model = SentenceTransformer(EMBED_MODEL)


def retrieve(question, k=TOP_K):
    """Retourne les k chunks les plus pertinents pour une question, avec leur source."""
    # 1) embedder la question (préfixe "query:" obligatoire pour e5)
    q_emb = _model.encode(f"query: {question}", normalize_embeddings=True)

    # 2) chercher les chunks les plus proches (distance cosinus <=>)
    with psycopg.connect(**DB) as conn:
        register_vector(conn)
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT c.content, d.titre, d.source_url,
                       c.embedding <=> %s AS distance
                FROM chunks c
                JOIN documents d ON d.id = c.document_id
                ORDER BY c.embedding <=> %s
                LIMIT %s
                """,
                (q_emb, q_emb, k),
            )
            rows = cur.fetchall()

    # 3) mettre en forme
    return [
        {"content": r[0], "titre": r[1], "source_url": r[2], "distance": r[3]}
        for r in rows
    ]


if __name__ == "__main__":
    question = "Comment générer un certificat SSL ?"
    print(f"❓ Question : {question}\n")
    for i, r in enumerate(retrieve(question), 1):
        similarite = 1 - r["distance"]      # distance -> similarité (approx)
        print(f"--- Résultat {i}  (similarité {similarite:.3f}) ---")
        print(f"📄 Source : {r['titre']}  [{r['source_url']}]")
        print(r["content"][:250].strip(), "...\n")