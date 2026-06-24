cat > /share/Docker/T-GLASS/app/tradernet/__init__.py << 'EOF'
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
TraderNet SDK для T-GLASS
"""

import sys
import os

# Добавляем текущую директорию в путь
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Импортируем из файлов в папке
try:
    from .core import Core
    from .tradernet_websocket import TradernetWebsocket
    print("✅ tradernet loaded from local files")
except ImportError as e:
    print(f"⚠️ Import error: {e}")
    
    # Заглушка
    class Core:
        def __init__(self, public_key=None, private_key=None):
            self.public_key = public_key
            self.private_key = private_key
            print("⚠️ TraderNet Core stub")
    
    class TradernetWebsocket:
        def __init__(self, core=None):
            self.core = core
            print("⚠️ TraderNet WebSocket stub")
        
        async def __aenter__(self):
            return self
        
        async def __aexit__(self, *args):
            pass
        
        async def quotes(self, ticker):
            import asyncio, random
            print(f"📡 [SIM] Starting quotes for {ticker}")
            price = 100.0
            counter = 0
            while True:
                await asyncio.sleep(2)
                counter += 1
                price += random.uniform(-0.5, 0.5)
                yield {
                    "ltp": round(price, 4),
                    "lts": random.randint(100, 3000),
                    "trades": counter,
                    "init": 0
                }
        
        async def market_depth(self, ticker):
            import asyncio
            print(f"📚 [SIM] Starting market depth for {ticker}")
            while True:
                await asyncio.sleep(1)
                yield {
                    "bids": [[100.0, 1000], [99.5, 2000]],
                    "asks": [[100.5, 1500], [101.0, 2500]]
                }

__all__ = ['Core', 'TradernetWebsocket']

print("✅ TraderNet module initialized")
EOF