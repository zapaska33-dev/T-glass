# На Asustor
cat > /share/Docker/T-GLASS/app/start.sh << 'EOF'
#!/bin/sh

echo "=========================================="
echo "🚀 T-GLASS v19.1 STARTUP SCRIPT"
echo "=========================================="

# Настройка путей
export PYTHONPATH=/app:/app/tradernet
echo "📁 PYTHONPATH=$PYTHONPATH"

# Переход в директорию
cd /app
echo "📁 WORKDIR=$(pwd)"

# Установка зависимостей
echo ""
echo "📦 Установка зависимостей..."
pip install --no-cache-dir aiohttp requests python-dotenv platformdirs maxapi

# Проверка импорта tradernet
echo ""
echo "🔍 Проверка импорта tradernet..."
python -c "
import sys
sys.path.insert(0, '/app')
sys.path.insert(0, '/app/tradernet')
try:
    from tradernet import Core, TradernetWebsocket
    print('✅ tradernet импортирован успешно')
except ImportError as e:
    print(f'❌ Ошибка импорта tradernet: {e}')
    exit(1)
"

# Проверка наличия файлов
echo ""
echo "📋 Проверка файлов проекта..."
ls -la /app/*.py | head -10

# Запуск основного приложения
echo ""
echo "=========================================="
echo "🚀 Запуск T-GLASS..."
echo "=========================================="
python /app/t-glass.py
EOF

# Делаем исполняемым
chmod +x /share/Docker/T-GLASS/app/start.sh