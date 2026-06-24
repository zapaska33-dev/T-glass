FROM python:3.10-slim

LABEL maintainer="T-GLASS Team"
LABEL version="19.1"

WORKDIR /app

# Установка системных зависимостей
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Копирование и установка зависимостей
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Копирование всего проекта (включая папку tradernet)
COPY . .

# Создание директорий
RUN mkdir -p /data/logs

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:80/health || exit 1

# Запуск
CMD ["sh", "/app/start.sh"]