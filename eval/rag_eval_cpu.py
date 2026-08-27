import os
import sys
import json
import time
from pathlib import Path

sys.path.append(os.path.join("backend", "app", "rag"))
from retriever import retrieve

GOLDEN = Path("eval/golden_dataset.json")


def main():
    golden = json.loads(GOLDEN.read_text(encoding="utf-8"))
    hits, latencies = 0, []
    for item in golden:
        q = item["question"]
        src = item.get("source", "")
        t0 = time.perf_counter()
        chunks = retrieve(q, k=4)
        latencies.append(time.perf_counter() - t0)
        retrieved_sources = {c["source_url"] for c in chunks}
        if src and src in retrieved_sources:
            hits += 1

    n = len(golden)
    latencies.sort()
    p50 = latencies[len(latencies) // 2]
    p95 = latencies[min(int(len(latencies) * 0.95), n - 1)]

    print(f"📊 Évaluation RAG (retrieval) sur {n} questions")
    print(f"🎯 Hit-rate @4 (bonne source récupérée) : {hits/n:.0%}  ({hits}/{n})")
    print(f"⏱️  Latence retrieval — P50 {p50*1000:.0f} ms · P95 {p95*1000:.0f} ms")


if __name__ == "__main__":
    main()