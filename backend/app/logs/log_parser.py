import re
import pandas as pd
from pathlib import Path

LOG_FILE = Path("data/raw/logs/access.log")

# Regex du Combined Log Format (groupes nommés)
PATTERN = re.compile(
    r'(?P<ip>\S+) \S+ \S+ \[(?P<time>[^\]]+)\] '
    r'"(?P<method>\S+) (?P<path>\S+) [^"]*" '
    r'(?P<status>\d{3}) (?P<size>\S+) '
    r'"(?P<referer>[^"]*)" "(?P<ua>[^"]*)"'
)


def parse_logs(path=LOG_FILE):
    rows = []
    for line in path.read_text(encoding="utf-8").splitlines():
        m = PATTERN.match(line)
        if m:
            rows.append(m.groupdict())
    df = pd.DataFrame(rows)
    df["status"] = df["status"].astype(int)
    df["time"] = pd.to_datetime(df["time"], format="%d/%b/%Y:%H:%M:%S %z")
    return df


if __name__ == "__main__":
    df = parse_logs()
    print(df.head(), "\n")
    print(f"✅ {len(df)} lignes parsées.")
    print("\nRépartition des statuts :")
    print(df["status"].value_counts())