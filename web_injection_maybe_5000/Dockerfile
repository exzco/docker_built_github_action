FROM python:3.11-slim

WORKDIR /app

ENV PYTHONUNBUFFERED=1 \
    APP_ORIGIN="http://127.0.0.1:5000"

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt && \
    python -m playwright install chromium --with-deps && \
    rm -rf /var/lib/apt/lists/*

COPY . .

EXPOSE 5000
CMD ["python", "app.py"]
