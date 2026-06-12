FROM python:3.10-slim

LABEL maintainer="T-GLASS Team"
LABEL version="19.1"
LABEL description="T-GLASS Order Flow Detector for TECHSMART"

# Установка рабочей директории
WORKDIR /app

# Установка системных зависимостей
RUN apt-get update && apt-get install -y \
    gcc \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# Копирование requirements.txt и установка зависимостей Python
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Копирование исходного кода
COPY . .

# Создание директорий для данных и логов
RUN mkdir -p /data /data/logs

# Настройка прав
RUN chmod +x t-glass.py

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:80/health || exit 1

# Запуск приложения
CMD ["python", "t-glass.py"]