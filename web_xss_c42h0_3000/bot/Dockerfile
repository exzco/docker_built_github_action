FROM node:20-slim

WORKDIR /app

ENV DEBIAN_FRONTEND=noninteractive
ENV PUPPETEER_SKIP_CHROMIUM_DOWNLOAD=true
ENV CHROMIUM_PATH=/usr/bin/chromium

RUN sed -i 's/deb.debian.org/mirrors.tuna.tsinghua.edu.cn/g' /etc/apt/sources.list.d/debian.sources 2>/dev/null || sed -i 's/deb.debian.org/mirrors.tuna.tsinghua.edu.cn/g' /etc/apt/sources.list \
    && apt-get update \
    && apt-get install -y --no-install-recommends \
        chromium \
        fonts-freefont-ttf \
    && rm -rf /var/lib/apt/lists/*

COPY package.json .
RUN npm install --omit=dev --registry=https://registry.npmmirror.com

COPY bot.js .

EXPOSE 5000

CMD ["node", "bot.js"]
