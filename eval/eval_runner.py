import os
import sys
import json
from pathlib import Path

sys.path.append(os.path.join("backend", "app", "rag"))
from rag_chain import answer as rag_answer          # notre RAG

from datasets import Dataset
from ragas import evaluate
from ragas.metrics import faithfulness, answer_relevancy
from ragas.llms import LangchainLLMWrapper
from ragas.embeddings import LangchainEmbeddingsWrapper
from langchain_ollama import ChatOllama
from langchain_huggingface import HuggingFaceEmbeddings

GOLDEN = Path("eval/golden_dataset.json")
OUT = Path("eval/ragas_results.json")
LIMIT = 2                       # 2 pour tester sur CPU ; passe à 30 sur GPU
LLM_MODEL = "qwen2.5:1.5b"      # deviendra "qwen2.5:3b" sur GPU


def main():
    golden = json.loads(GOLDEN.read_text(encoding="utf-8"))[:LIMIT]

    rows = []
    for i, item in enumerate(golden, 1):
        q = item["question"]
        print(f"[{i}/{len(golden)}] RAG : {q[:55]}...")
        ans, chunks = rag_answer(q)
        rows.append({
            "question": q,
            "answer": ans,
            "contexts": [c["content"] for c in chunks],
            "ground_truth": item["ground_truth"],
        })

    dataset = Dataset.from_list(rows)

    llm = LangchainLLMWrapper(ChatOllama(model=LLM_MODEL))
    emb = LangchainEmbeddingsWrapper(
        HuggingFaceEmbeddings(model_name="intfloat/multilingual-e5-small")
    )

    print("\n⏳ Évaluation RAGAS (lente sur CPU, patiente)...")
    result = evaluate(dataset, metrics=[faithfulness, answer_relevancy],
                      llm=llm, embeddings=emb)

    print("\n🎯 Scores RAGAS :")
    print(result)
    result.to_pandas().to_json(OUT, orient="records", force_ascii=False, indent=2)
    print(f"\n✅ Détails sauvegardés : {OUT}")


if __name__ == "__main__":
    main()