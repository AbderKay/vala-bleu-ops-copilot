FROM python:3.11-slim

WORKDIR /app

# Dépendances système minimales
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential && rm -rf /var/lib/apt/lists/*

# Dépendances Python
# torch CPU (bien plus léger que la version CUDA) — embeddings sur CPU, le LLM est géré par Ollama
RUN pip install --no-cache-dir torch --index-url https://download.pytorch.org/whl/cpu
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Code de l'application
COPY backend/ ./backend/
COPY db/ ./db/
COPY frontend/index.html ./frontend/index.html

EXPOSE 8000
CMD ["python", "backend/app/main.py"]
