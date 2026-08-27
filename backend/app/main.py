import os
import sys

# rendre importables les sous-modules rag / logs / router
BASE = os.path.dirname(__file__)
for sub in ("rag", "logs", "router"):
    sys.path.append(os.path.join(BASE, sub))

from pathlib import Path
from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from pydantic import BaseModel

from rag_chain import answer as rag_answer, smalltalk    # RAG + conversation
from router_ml import route                     # routeur
from log_analysis import analyze_logs, analyze_stream   # logs (batch + speed)


app = FastAPI(title="Vala Bleu Ops Copilot", version="1.0")

# Interface web custom servie à la racine "/"
FRONTEND = Path(__file__).resolve().parent.parent.parent / "frontend" / "index.html"


@app.get("/", response_class=HTMLResponse)
def home():
    return FRONTEND.read_text(encoding="utf-8")


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

    if intent == "AUTRE":                     # 2c) conversation hors-sujet
        answer_text = smalltalk(req.question)

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


@app.post("/logs/stream")
def logs_stream():
    return analyze_stream()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)