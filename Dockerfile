FROM python:3.12-slim
WORKDIR /app
COPY backend/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt
COPY alembic.ini .
COPY backend backend
RUN useradd --create-home app && mkdir -p /data && chown app:app /data
USER app
ENV PORT=8000 DATABASE_URL=sqlite:////data/ecocycle.db FORECAST_MODEL_PATH=/data/forecast.json
EXPOSE 8000
CMD ["sh","-c","alembic upgrade head && uvicorn backend.main:app --host 0.0.0.0 --port ${PORT}"]
