#!/bin/sh
set -e

# 启动 Bot 服务（运行在 127.0.0.1:5000）
cd /app/bot
node bot.js &

# 启动 Flask Web 服务（前台运行在 0.0.0.0:3000）
cd /app/web
exec python3 app.py
