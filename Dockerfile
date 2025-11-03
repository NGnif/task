FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Set environment defaults (override in deploy)
ENV PORT=5000 \
    GUNICORN_CMD_ARGS="--workers=3 --threads=2 --timeout=60"

EXPOSE 5000

CMD ["gunicorn", "run:app", "-b", "0.0.0.0:5000"]

