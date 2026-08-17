FROM python:3.12-slim
WORKDIR /app
COPY backend/requirements.txt backend/requirements.txt
RUN pip install --no-cache-dir -r backend/requirements.txt
COPY backend backend
COPY alembic alembic
COPY alembic.ini .
ENV PYTHONUNBUFFERED=1 DATABASE_PATH=/data/cashflow.db
RUN mkdir -p /data
EXPOSE 8000
CMD ["sh", "-c", "alembic upgrade head && uvicorn backend.api:app --host 0.0.0.0 --port 8000"]