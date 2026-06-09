FROM python:3.10-slim

# Установка платформы для ARM64
ARG TARGETPLATFORM=linux/arm64
ARG BUILDPLATFORM=linux/arm64

WORKDIR /app

# Установка зависимостей
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копирование кода
COPY . .

# Создание директорий для данных
RUN mkdir -p /data /data/logs

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:80/health')" || exit 1

# Запуск
CMD ["python", "t-glass.py"]