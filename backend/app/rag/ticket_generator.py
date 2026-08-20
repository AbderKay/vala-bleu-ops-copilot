import random
from pathlib import Path
import frontmatter
from datetime import date

DOCS_DIR = Path("data/raw/vala_bleu_public")
OUT_DIR = Path("data/raw/tickets")
N_TICKETS = 40

FAKE_IPS = ["41.92.10.55", "196.200.14.7", "105.66.3.180", "192.168.1.42"]
FAKE_EMAILS = ["client{n}@gmail.com", "user{n}@hotmail.fr", "site{n}@vala.ma"]
FAKE_PHONES = ["0612345678", "0655098721", "0700112233"]

TEMPLATES = [
    "Bonjour, j'ai un souci : {sujet}. Mon IP est {ip}, email {email}. Merci.",
    "Je n'arrive pas à gérer : {sujet}. Rappelez-moi au {phone}. Email : {email}.",
    "Urgent : {sujet}. Serveur concerné {ip}, contact {email}.",
    "Question sur {sujet}. Compte lié à {email}, tél {phone}.",
]


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    docs = sorted(DOCS_DIR.glob("*.md"))
    random.seed(42)  # reproductible
    chosen = random.sample(docs, min(N_TICKETS, len(docs)))

    for i, f in enumerate(chosen, 1):
        post = frontmatter.load(f)
        titre = post.metadata.get("titre", "Problème technique")
        categorie = post.metadata.get("categorie", "autre")
        resolution = post.content.strip().split("\n", 1)[-1].strip()[:400]

        ip = random.choice(FAKE_IPS)
        email = random.choice(FAKE_EMAILS).format(n=i)
        phone = random.choice(FAKE_PHONES)
        message = random.choice(TEMPLATES).format(sujet=titre, ip=ip, email=email, phone=phone)

        md = (
            "---\n"
            f'titre: "Ticket #{i:03d} — {titre}"\n'
            f'source_url: "ticket-interne-{i:03d}"\n'
            f'categorie: "{categorie}"\n'
            'type: "ticket"\n'
            f'date_collecte: "{date.today()}"\n'
            'langue: "fr"\n'
            "---\n\n"
            f"# Ticket #{i:03d} — {titre}\n\n"
            f"**Message client :** {message}\n\n"
            f"**Résolution :** {resolution}\n"
        )
        (OUT_DIR / f"ticket-{i:03d}.md").write_text(md, encoding="utf-8")

    print(f"✅ {len(chosen)} tickets synthétiques générés dans {OUT_DIR}")


if __name__ == "__main__":
    main()