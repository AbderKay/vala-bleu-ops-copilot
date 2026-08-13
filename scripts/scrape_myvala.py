import time
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from pathlib import Path
from datetime import date

BASE = "https://www.myvala.com"
KB = f"{BASE}/knowledgebase"
HEADERS = {"User-Agent": "Mozilla/5.0 (ValaBleuKB-PFA; educational project)"}
OUT_DIR = Path("data/raw/vala_bleu_public")

# Suffixe ajouté par le site dans <title>, à retirer
TITLE_SUFFIX = " - Automatisation Intelligente des Solutions Web"
# Textes parasites en fin d'article, à couper
BOILERPLATE = [
    "Vous ne trouvez pas l'information",
    "Créer un Ticket de Support",
    "L'avez-vous trouvé utile",
]


def get_soup(url):
    resp = requests.get(url, headers=HEADERS, timeout=20)
    resp.raise_for_status()
    resp.encoding = resp.apparent_encoding
    return BeautifulSoup(resp.text, "lxml")


def normalize(href):
    href = href.split("?")[0].split("#")[0]
    href = urljoin(BASE + "/", href)
    href = href.replace("https://myvala.com", "https://www.myvala.com")
    return href.rstrip("/")


def get_category_urls():
    soup = get_soup(KB)
    urls = set()
    for a in soup.select("a[href]"):
        href = normalize(a["href"])
        if "/knowledgebase/" in href:
            urls.add(href)
    return sorted(urls)


def get_article_urls(category_url):
    soup = get_soup(category_url)
    urls = set()
    for a in soup.select("a[href]"):
        href = normalize(a["href"])
        if "/info/" in href:
            urls.add(href)
    return urls


def clean_content(content, title):
    """Enlève le titre répété en 1re ligne + coupe le texte parasite final."""
    lines = [l.strip() for l in content.split("\n")]
    if lines and lines[0] == title:      # 1re ligne = titre répété -> on l'enlève
        lines = lines[1:]
    cleaned = []
    for l in lines:
        if any(b in l for b in BOILERPLATE):   # début du parasite -> on s'arrête
            break
        cleaned.append(l)
    return "\n".join(cleaned).strip()


def scrape_article(url):
    """Télécharge un article, renvoie (titre, contenu propre)."""
    soup = get_soup(url)
    # Titre depuis <title>, sans le suffixe du site
    raw_title = soup.title.get_text(strip=True) if soup.title else ""
    if raw_title.endswith(TITLE_SUFFIX):
        title = raw_title[: -len(TITLE_SUFFIX)].strip()
    else:
        title = raw_title or "Sans titre"
    # Contenu
    content_el = soup.select_one("div.sayfacontent")
    content = content_el.get_text("\n", strip=True) if content_el else ""
    content = clean_content(content, title)
    return title, content


def save_article(title, content, url, category):
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    slug = url.rstrip("/").split("/")[-1]
    safe_title = title.replace('"', "'")
    md = (
        "---\n"
        f'titre: "{safe_title}"\n'
        f'source_url: "{url}"\n'
        f'categorie: "{category}"\n'
        f'date_collecte: "{date.today()}"\n'
        'langue: "fr"\n'
        "---\n\n"
        f"# {title}\n\n"
        f"{content}\n"
    )
    (OUT_DIR / f"{slug}.md").write_text(md, encoding="utf-8")


if __name__ == "__main__":
    categories = get_category_urls()
    print(f"✅ {len(categories)} catégories trouvées\n")

    seen = set()
    ok, fail = 0, 0
    for cat in categories:
        cat_name = cat.split("/")[-1]
        for art_url in sorted(get_article_urls(cat)):
            if art_url in seen:
                continue
            seen.add(art_url)
            try:
                title, content = scrape_article(art_url)
                save_article(title, content, art_url, cat_name)
                ok += 1
                print(f"  ✅ [{cat_name}] {title[:55]}")
                time.sleep(0.5)
            except Exception as e:
                fail += 1
                print(f"  ❌ {art_url} -> {e}")

    print(f"\n🎯 Terminé : {ok} articles sauvegardés, {fail} échecs")
    print(f"📁 Dossier : {OUT_DIR.resolve()}")