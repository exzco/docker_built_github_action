FROM python:3.11-slim
WORKDIR /app
RUN pip config set global.index-url https://mirrors.aliyun.com/pypi/simple/ && \
    pip install --no-cache-dir flask
COPY app.py .
CMD ["python", "app.py"]