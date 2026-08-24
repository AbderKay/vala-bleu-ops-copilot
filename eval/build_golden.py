import json
import random
from pathlib import Path
import frontmatter

DOCS = Path("data/raw/vala_bleu_public")
OUT = Path("eval/golden_dataset.json")
N = 30


def main():
    OUT.parent.mkdir(parents=True, exist_ok=True)
    files = sorted(DOCS.glob("*.md"))
    random.seed(123)
    chosen = random.sample(files, min(N, len(files)))

    dataset = []
    for f in chosen:
        post = frontmatter.load(f)
        titre = str(post.metadata.get("titre", "")).strip()
        if not titre:
            continue
        question = titre if titre.endswith("?") else f"{titre} ?"
        # réponse de référence = contenu réel du document (nettoyé)
        body = post.content.strip().split("\n", 1)[-1].strip()
        ground_truth = " ".join(body.split())[:600]
        dataset.append({
            "question": question,
            "ground_truth": ground_truth,
            "source": post.metadata.get("source_url", ""),
        })

    OUT.write_text(json.dumps(dataset, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"✅ Golden dataset : {len(dataset)} paires Q/R → {OUT}")


if __name__ == "__main__":
    main()