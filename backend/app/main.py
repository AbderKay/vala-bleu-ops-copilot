import os
import sys

# rendre importables les sous-modules rag / logs / router
BASE = os.path.dirname(__file__)
for sub in ("rag", "logs", "router"):
    sys.path.append(os.path.join(BASE, sub))

from fastapi import FastAPI
from pydantic import BaseModel

from rag_chain import answer as rag_answer      # RAG
from router_ml import route                     # routeur
from log_analysis import analyze_logs           # logs

app = FastAPI(title="Vala Bleu Ops Copilot", version="1.0")


class ChatRequest(BaseModel):
    question: str


class ChatResponse(BaseModel):
    intent: str
    answer: str
    sources: list = []
    logs: dict | None = None


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/chat", response_model=ChatResponse)
def chat(req: ChatRequest):
    intent = route(req.question)              # 1) router l'intention
    answer_text, sources, logs = "", [], None

    if intent in ("RAG", "MIXTE"):            # 2a) volet connaissance
        answer_text, chunks = rag_answer(req.question)
        sources = [{"titre": c["titre"], "source_url": c["source_url"]} for c in chunks]

    if intent in ("LOGS", "MIXTE"):           # 2b) volet état système
        logs = analyze_logs()
        if intent == "LOGS":
            answer_text = (f"{logs['n_anomalies']} IP anormale(s) détectée(s) "
                           f"sur {logs['total_ips']} au total.")

    return ChatResponse(intent=intent, answer=answer_text, sources=sources, logs=logs)


@app.post("/logs/analyze")
def logs_analyze():
    return analyze_logs()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)