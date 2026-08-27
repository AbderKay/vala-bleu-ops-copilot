FROM python:3.11-slim

WORKDIR /app

RUN pip install --no-cache-dir streamlit requests pandas

COPY frontend/ ./frontend/
COPY .streamlit/ ./.streamlit/

EXPOSE 8501
CMD ["streamlit", "run", "frontend/app.py", "--server.address=0.0.0.0", "--server.port=8501"]
