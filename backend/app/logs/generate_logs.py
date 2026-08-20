import random
from datetime import datetime, timedelta
from pathlib import Path

OUT = Path("data/raw/logs/access.log")
N_NORMAL = 5000

random.seed(42)
IPS = [f"196.200.{random.randint(0,255)}.{random.randint(1,254)}" for _ in range(50)]
PATHS = ["/", "/index.html", "/produits", "/contact", "/blog/article-1",
         "/api/status", "/images/logo.png", "/css/style.css", "/login", "/panier"]
UAS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 16_0) Safari/604.1",
    "Mozilla/5.0 (X11; Linux x86_64) Firefox/121.0",
]
STATUS = [200, 200, 200, 200, 200, 304, 404, 301]   # majorité de 200


def gen_line(ip, ts, path, status, ua):
    size = random.randint(200, 5000)
    return (f'{ip} - - [{ts.strftime("%d/%b/%Y:%H:%M:%S +0000")}] '
            f'"GET {path} HTTP/1.1" {status} {size} "-" "{ua}"')


def main():
    OUT.parent.mkdir(parents=True, exist_ok=True)
    t = datetime(2026, 8, 20, 8, 0, 0)
    lines = []
    for _ in range(N_NORMAL):
        t += timedelta(seconds=random.randint(0, 5))
        lines.append(gen_line(random.choice(IPS), t, random.choice(PATHS),
                              random.choice(STATUS), random.choice(UAS)))
    OUT.write_text("\n".join(lines), encoding="utf-8")
    print(f"✅ {len(lines)} lignes de logs générées dans {OUT}")


if __name__ == "__main__":
    main()