cat > /share/Docker/T-GLASS/app/start.sh << 'EOF'
#!/bin/sh

echo "=========================================="
echo "🚀 T-GLASS v19.1 STARTUP SCRIPT"
echo "=========================================="

# Принудительная настройка путей
export PYTHONPATH=/app:/app/tradernet:/usr/local/lib/python3.10/site-packages
export PYTHONUNBUFFERED=1

echo "📁 PYTHONPATH=$PYTHONPATH"

cd /app
echo "📁 WORKDIR=$(pwd)"

echo ""
echo "📦 Установка зависимостей..."
pip install --no-cache-dir aiohttp requests python-dotenv platformdirs maxapi

echo ""
echo "🔍 Проверка структуры tradernet..."
ls -la /app/tradernet/

echo ""
echo "🔍 Проверка импорта tradernet..."
python -c "
import sys
print('=== sys.path ===')
for p in sys.path:
    print(f'  {p}')
print('=== Проверка импорта ===')
try:
    from tradernet import Core, TradernetWebsocket
    print('✅ tradernet импортирован успешно')
except ImportError as e:
    print(f'❌ Ошибка импорта tradernet: {e}')
    # Создаем заглушку
    class Core:
        def __init__(self, *args, **kwargs):
            print('⚠️ Core stub')
    class TradernetWebsocket:
        def __init__(self, *args, **kwargs):
            print('⚠️ WebSocket stub')
        async def __aenter__(self): return self
        async def __aexit__(self, *args): pass
        async def quotes(self, ticker):
            import asyncio, random
            while True:
                await asyncio.sleep(2)
                yield {'ltp': 100.0, 'lts': 1000, 'trades': 1, 'init': 0}
        async def market_depth(self, ticker):
            import asyncio
            while True:
                await asyncio.sleep(1)
                yield {'bids': [[100.0, 1000]], 'asks': [[100.5, 1500]]}
    print('⚠️ Используется заглушка tradernet')
"

echo ""
echo "=========================================="
echo "🚀 Запуск T-GLASS..."
echo "=========================================="
python /app/t-glass.py
EOF

chmod +x /share/Docker/T-GLASS/app/start.sh