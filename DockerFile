FROM python:3.10-slim

LABEL maintainer="T-GLASS Team"
LABEL version="19.1"

WORKDIR /app

# Установка системных зависимостей
RUN apt-get update && apt-get install -y \
    gcc \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# Копирование и установка TraderNet SDK (ДО копирования остального кода)
COPY tradernet_sdk-2.0.0.tar.gz .
RUN pip install --no-cache-dir tradernet_sdk-2.0.0.tar.gz

# Проверка установки
RUN python -c "from tradernet import Core, TradernetWebsocket; print('✅ tradernet installed successfully')"

# Копирование requirements.txt и установка остальных зависимостей
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копирование исходного кода
COPY . .

# Создание директорий
RUN mkdir -p /data /data/logs

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:80/health || exit 1

CMD ["python", "t-glass.py"]