FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source
COPY . .

# Warm up models to avoid cold starts on boot
RUN python -c "from app.models.embedding_model import get_embedding_model; get_embedding_model()"
RUN python -c "from app.models.reranker_model import get_reranker_model; get_reranker_model()"

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8001"]
