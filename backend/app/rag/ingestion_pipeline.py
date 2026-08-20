import os
import sys
from pathlib import Path
import frontmatter
from dotenv import load_dotenv
import psycopg
from pgvector.psycopg import register_vector
from sentence_transformers import SentenceTransformer
from langchain_text_splitters import RecursiveCharacterTextSplitter

sys.path.append(os.path.dirname(__file__))
from anonymizer import anonymize            # ① l'anonymiseur

load_dotenv(override=True)

DATA_DIRS = [                                # ② doc publique + tickets
    Path("data/raw/vala_bleu_public"),
    Path("data/raw/tickets"),
]
EMBED_MODEL = "intfloat/multilingual-e5-small"

DB = dict(
    host="localhost",
    port=int(os.environ.get("POSTGRES_PORT", "5433").strip()),
    dbname=os.environ["POSTGRES_DB"].strip(),
    user=os.environ["POSTGRES_USER"].strip(),
    password=os.environ["POSTGRES_PASSWORD"].strip(),
)


def main():
    print("⏳ Chargement du modèle d'embeddings...")
    model = SentenceTransformer(EMBED_MODEL)
    splitter = RecursiveCharacterTextSplitter(chunk_size=800, chunk_overlap=100)

    files = []
    for d in DATA_DIRS:
        files += sorted(d.glob("*.md"))
    print(f"📄 {len(files)} documents à ingérer.\n")

    total_redactions = {}
    with psycopg.connect(**DB) as conn:
        register_vector(conn)
        with conn.cursor() as cur:
            cur.execute("TRUNCATE documents, chunks RESTART IDENTITY CASCADE;")
            total_chunks = 0
            for f in files:
                post = frontmatter.load(f)
                meta, body = post.metadata, post.content

                body, report = anonymize(body)          # ③ anonymisation AVANT stockage
                for k, v in report.items():
                    total_redactions[k] = total_redactions.get(k, 0) + v

                cur.execute(
                    """INSERT INTO documents (source_url, titre, categorie, langue, date_collecte)
                       VALUES (%s,%s,%s,%s,%s) RETURNING id""",
                    (meta.get("source_url"), meta.get("titre"), meta.get("categorie"),
                     meta.get("langue", "fr"), meta.get("date_collecte")),
                )
                doc_id = cur.fetchone()[0]

                chunks = splitter.split_text(body)
                if not chunks:
                    continue
                inputs = [f"passage: {c}" for c in chunks]
                embeddings = model.encode(inputs, normalize_embeddings=True)
                for i, (c, emb) in enumerate(zip(chunks, embeddings)):
                    cur.execute(
                        """INSERT INTO chunks (document_id, chunk_index, content, embedding)
                           VALUES (%s,%s,%s,%s)""",
                        (doc_id, i, c, emb),
                    )
                total_chunks += len(chunks)
        conn.commit()
    print(f"🎯 Ingestion terminée : {len(files)} documents, {total_chunks} chunks.")
    print(f"🔒 PII anonymisées : {total_redactions or 'aucune'}")


if __name__ == "__main__":
    main()