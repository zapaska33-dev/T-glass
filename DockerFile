cd /share/Docker/T-glass

cat > Dockerfile << 'EOF'
FROM python:3.10-slim

WORKDIR /app

# Копируем SDK и requirements
COPY tradernet_sdk-2.0.0.tar.gz .
COPY requirements.txt .

# Устанавливаем зависимости
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install --no-cache-dir ./tradernet_sdk-2.0.0.tar.gz

# Копируем код
COPY . .

# Создаем директории
RUN mkdir -p /data/logs

CMD ["python", "t-glass.py"]
EOF