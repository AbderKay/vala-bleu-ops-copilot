import os
from pathlib import Path
import frontmatter
from dotenv import load_dotenv
import psycopg
from pgvector.psycopg import register_vector
from sentence_transformers import SentenceTransformer
from langchain_text_splitters import RecursiveCharacterTextSplitter

load_dotenv(override=True)  # charge .env ET écrase toute variable système parasite

DATA_DIR = Path("data/raw/vala_bleu_public")
EMBED_MODEL = "intfloat/multilingual-e5-small"   # 384 dim (CPU) — deviendra e5-large sur GPU

DB = dict(
    host="localhost",
    port=int(os.environ.get("POSTGRES_PORT", "5433").strip()),
    dbname=os.environ["POSTGRES_DB"].strip(),
    user=os.environ["POSTGRES_USER"].strip(),
    password=os.environ["POSTGRES_PASSWORD"].strip(),
)


def main():
    print("⏳ Chargement du modèle d'embeddings (1er lancement = téléchargement)...")
    model = SentenceTransformer(EMBED_MODEL)
    splitter = RecursiveCharacterTextSplitter(chunk_size=800, chunk_overlap=100)

    files = sorted(DATA_DIR.glob("*.md"))
    print(f"📄 {len(files)} documents à ingérer.\n")

    with psycopg.connect(**DB) as conn:
        register_vector(conn)
        with conn.cursor() as cur:
            # on repart propre -> permet de relancer sans doublons
            cur.execute("TRUNCATE documents, chunks RESTART IDENTITY CASCADE;")

            total_chunks = 0
            for f in files:
                post = frontmatter.load(f)
                meta, body = post.metadata, post.content

                # 1) insérer le document (et récupérer son id)
                cur.execute(
                    """INSERT INTO documents (source_url, titre, categorie, langue, date_collecte)
                       VALUES (%s,%s,%s,%s,%s) RETURNING id""",
                    (meta.get("source_url"), meta.get("titre"), meta.get("categorie"),
                     meta.get("langue", "fr"), meta.get("date_collecte")),
                )
                doc_id = cur.fetchone()[0]

                # 2) découper en chunks
                chunks = splitter.split_text(body)
                if not chunks:
                    continue

                # 3) embedder (préfixe "passage:" obligatoire pour e5)
                inputs = [f"passage: {c}" for c in chunks]
                embeddings = model.encode(inputs, normalize_embeddings=True)

                # 4) insérer les chunks + leurs vecteurs
                for i, (c, emb) in enumerate(zip(chunks, embeddings)):
                    cur.execute(
                        """INSERT INTO chunks (document_id, chunk_index, content, embedding)
                           VALUES (%s,%s,%s,%s)""",
                        (doc_id, i, c, emb),
                    )
                total_chunks += len(chunks)
                print(f"  ✅ {str(meta.get('titre','?'))[:45]:45s} — {len(chunks)} chunks")

        conn.commit()
    print(f"\n🎯 Ingestion terminée : {len(files)} documents, {total_chunks} chunks.")


if __name__ == "__main__":
    main()
