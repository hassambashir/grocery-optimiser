FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt requirements-app.txt ./
RUN pip install --no-cache-dir -r requirements-app.txt
COPY app ./app
COPY scripts ./scripts
COPY data ./data
COPY config ./config
RUN useradd --create-home grocery && chown -R grocery:grocery /app
USER grocery
ENV PORT=8000 COOKIE_SECURE=true
CMD ["sh", "-c", "python -m uvicorn app.main:create_app --factory --host 0.0.0.0 --port ${PORT:-8000}"]
