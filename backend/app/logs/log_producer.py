import time
import random
from datetime import datetime
from pathlib import Path

STREAM = Path("data/raw/logs/access_stream.log")
IPS = [f"196.200.{random.randint(0,255)}.{random.randint(1,254)}" for _ in range(30)]
PATHS = ["/", "/index.html", "/produits", "/login", "/api/status"]
UA = "Mozilla/5.0 Chrome/120"


def line(ip, path, status):
    ts = datetime.now().strftime("%d/%b/%Y:%H:%M:%S +0000")
    return f'{ip} - - [{ts}] "GET {path} HTTP/1.1" {status} 400 "-" "{UA}"'


def main():
    STREAM.parent.mkdir(parents=True, exist_ok=True)
    print(f"🚦 Producteur de logs → {STREAM}  (Ctrl+C pour arrêter)")
    tick = 0
    with STREAM.open("a", encoding="utf-8") as f:
        while True:
            for _ in range(random.randint(3, 8)):          # trafic normal
                f.write(line(random.choice(IPS), random.choice(PATHS),
                             random.choice([200, 200, 304, 404])) + "\n")
            tick += 1
            if tick % 15 == 0:                             # ~ttes les 15s : attaque
                for _ in range(120):
                    f.write(line("45.13.66.201", "/login", 401) + "\n")
                print("💥 Attaque brute-force injectée !")
            f.flush()
            time.sleep(1)


if __name__ == "__main__":
    main()