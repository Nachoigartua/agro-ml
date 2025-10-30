# Backend ML
FROM python:3.9-slim

WORKDIR /app
ENV PYTHONPATH=/app
RUN mkdir -p /workspace/backend

# Instalar dependencias del sistema
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copiar requirements
COPY api/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar código fuente
COPY api/ .
COPY alembic.ini /workspace/backend/alembic.ini
COPY alembic /workspace/backend/alembic

# Comando por defecto
CMD ["sh", "-c", "until alembic -c /workspace/backend/alembic.ini upgrade head; do echo 'Alembic failed, retrying in 5 seconds...'; sleep 5; done; uvicorn app.main:app --host 0.0.0.0 --port 8000"]
