FROM node:20-slim

WORKDIR /app

ENV DEBIAN_FRONTEND=noninteractive \
    PUPPETEER_SKIP_CHROMIUM_DOWNLOAD=true \
    CHROMIUM_PATH=/usr/bin/chromium \
    PYTHONUNBUFFERED=1

RUN sed -i 's/deb.debian.org/mirrors.tuna.tsinghua.edu.cn/g' /etc/apt/sources.list.d/debian.sources 2>/dev/null || sed -i 's/deb.debian.org/mirrors.tuna.tsinghua.edu.cn/g' /etc/apt/sources.list \
    && apt-get update \
    && apt-get install -y --no-install-recommends \
        chromium \
        fonts-freefont-ttf \
        python3 \
        python3-flask \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app/bot
COPY bot/package.json .
RUN npm install --omit=dev --registry=https://registry.npmmirror.com
COPY bot/bot.js .

WORKDIR /app/web
COPY app/app.py .

WORKDIR /app
COPY start.sh .
RUN chmod +x start.sh

EXPOSE 3000

CMD ["/app/start.sh"]
