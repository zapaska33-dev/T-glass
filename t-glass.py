#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import asyncio
import os
import sys
import time
import json
import logging
from datetime import datetime
from collections import deque

# ========== НАСТРОЙКА ЛОГИРОВАНИЯ (в корне) ==========
def setup_logging():
    """Простая настройка логирования без внешних модулей"""
    # Создаем директорию для логов если нужно
    log_dir = '/data/logs'
    try:
        os.makedirs(log_dir, exist_ok=True)
    except:
        pass
    
    # Формат логов
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Основной логгер
    logger = logging.getLogger('tglass')
    logger.setLevel(logging.INFO)
    
    # Консольный handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # Файловый handler (если есть доступ)
    try:
        file_handler = logging.FileHandler(f'{log_dir}/tglass.log')
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    except:
        pass
    
    # Логгер для трейдов
    logger_trade = logging.getLogger('trade')
    logger_trade.setLevel(logging.INFO)
    logger_trade.addHandler(console_handler)
    
    # Логгер для AI
    logger_ai = logging.getLogger('ai')
    logger_ai.setLevel(logging.INFO)
    logger_ai.addHandler(console_handler)
    
    return logger, logger_trade, logger_ai

# Инициализация логов
logger, logger_trade, logger_ai = setup_logging()

# ========== КОНФИГУРАЦИЯ ==========
TICKER = os.environ.get('TRADERNET_TICKER', 'TECHSMART')
MAX_SCORE = 100

# ========== СТАТИСТИКА ==========
class Stats:
    def __init__(self):
        self.start = time.time()
        self.trades = 0
        self.qualified = 0
        self.alerts = 0
        self.ai_req = 0
        self.ai_ok = 0
        self.ai_no = 0
        self.book_updates = 0
        self.delta = 0
        self.detector_hits = {}
        self.duplicates_skipped = 0
        self.total_cost = 0.0

stats = Stats()
recent_trades = deque(maxlen=10000)

# ========== ДЕТЕКТОРЫ ==========
class SignalType:
    ABSORPTION = "absorption"
    PRICE_RESPONSE = "price_response"
    ICEBERG = "iceberg"
    IMBALANCE = "imbalance"
    SPOOFING = "spoofing"
    DELTA = "delta"
    WALL = "wall"
    LIQUIDITY_SHIFT = "liquidity_shift"
    TAPE_SPEED = "tape_speed"
    VOLUME_CLUSTER = "volume_cluster"
    TRADE_VELOCITY = "trade_velocity"

class DetectorJournal:
    def __init__(self):
        self.detectors = {}
        self.bias = 0
    
    def set(self, signal_type, value, details, direction):
        self.detectors[signal_type] = {
            'value': value,
            'details': details,
            'direction': direction,
            'timestamp': time.time()
        }
        logger.warning(f"🔔 {signal_type}: {details}")
    
    def calc(self, delta):
        score = 0
        bullish = 0
        bearish = 0
        now = time.time()
        
        weights = {
            SignalType.DELTA: 40,
            SignalType.SPOOFING: 30,
            SignalType.ABSORPTION: 10,
            SignalType.PRICE_RESPONSE: 15,
            SignalType.ICEBERG: 5,
            SignalType.IMBALANCE: 10,
            SignalType.WALL: 15,
            SignalType.LIQUIDITY_SHIFT: 8,
            SignalType.TAPE_SPEED: 5,
            SignalType.VOLUME_CLUSTER: 7,
            SignalType.TRADE_VELOCITY: 5,
        }
        
        for st, det in self.detectors.items():
            if now - det['timestamp'] < 10:  # TTL 10 сек
                weight = weights.get(st, 10)
                score += weight
                if det['direction'] == 'BULLISH':
                    bullish += weight
                elif det['direction'] == 'BEARISH':
                    bearish += weight
        
        self.bias = (bullish - bearish) / max(score, 1) * 100
        return min(score, MAX_SCORE)
    
    def get_components(self):
        return {}
    
    def get_signals(self):
        return list(self.detectors.keys())

def detect_delta(journal):
    if abs(stats.delta) >= 7000:
        direction = "BULLISH" if stats.delta > 0 else "BEARISH"
        journal.set(SignalType.DELTA, {"delta": stats.delta}, f"Δ={stats.delta:+,}", direction)
        return True
    return False

def process_trade(price, volume, side):
    global stats
    
    stats.trades += 1
    
    # Обновление дельты
    if side == "BUY":
        stats.delta += volume
    elif side == "SELL":
        stats.delta -= volume
    
    # Сохраняем сделку
    recent_trades.append({
        'time': time.time(),
        'price': price,
        'volume': volume,
        'side': side
    })
    
    # Запуск детекторов
    journal = DetectorJournal()
    detect_delta(journal)
    
    score = journal.calc(stats.delta)
    bias = journal.bias
    
    logger_trade.info(f"Trade #{stats.trades}: {price:.4f} x {volume} {side} | Δ={stats.delta:+,}")
    logger.info(f"🎯 Score: {score}/{MAX_SCORE} | Bias: {bias:+.1f}")
    
    # Проверка сигнала
    required_score = int(os.environ.get('SETUP_SCORE_REQUIRED', 40))
    if score >= required_score:
        stats.qualified += 1
        direction = "LONG" if bias > 0 else "SHORT" if bias < 0 else "NONE"
        logger.warning(f"🚨 SIGNAL: {direction} | Score={score} | Bias={bias:+.1f} | Δ={stats.delta:+,}")
        
        # Отправка в MAX (если настроен)
        max_token = os.environ.get('MAX_BOT_TOKEN')
        if max_token and direction != "NONE":
            send_signal(price, volume, direction, score, bias)

def send_signal(price, volume, direction, score, bias):
    """Отправка сигнала в MAX Bot"""
    try:
        stats.alerts += 1
        stats.ai_ok += 1
        
        tick = 0.005
        if direction == "LONG":
            stop = price - 20 * tick
            target = price + 40 * tick
        else:
            stop = price + 20 * tick
            target = price - 40 * tick
        
        msg = f"""🚨 T-GLASS СИГНАЛ
{direction} | Уверенность: 85%
Оценка: {score} | Смещение: {bias:+.1f} | Дельта: {stats.delta:+,}
Вход: {price:.4f} | Стоп: {stop:.4f} | Цель: {target:.4f}"""
        
        logger.warning(f"📤 {msg}")
        # Здесь реальная отправка в MAX API
        
    except Exception as e:
        logger.error(f"Send error: {e}")

# ========== HTTP СЕРВЕР ==========
async def start_health_server():
    """Запуск health check сервера"""
    try:
        from aiohttp import web
        
        async def health(request):
            return web.json_response({
                "status": "ok",
                "version": "19.1",
                "name": "T-GLASS",
                "ticker": TICKER,
                "uptime": time.time() - stats.start,
                "trades": stats.trades,
                "delta": stats.delta,
                "signals": stats.alerts,
                "timestamp": datetime.now().isoformat()
            })
        
        app = web.Application()
        app.router.add_get("/health", health)
        app.router.add_get("/", health)
        
        runner = web.AppRunner(app)
        await runner.setup()
        site = web.TCPSite(runner, "0.0.0.0", 80)
        await site.start()
        
        logger.info("🏥 Health check: http://localhost:80/health")
        return True
    except ImportError:
        logger.warning("aiohttp not installed")
        return False
    except Exception as e:
        logger.error(f"Health server error: {e}")
        return False

# ========== СИМУЛЯЦИЯ ==========
async def simulate_trades():
    """Симуляция сделок для теста"""
    logger.info("📊 Demo mode: simulating trades...")
    
    demo_data = [
        (100.00, 1500, "BUY"), (100.50, 2000, "BUY"), (101.00, 3000, "BUY"),
        (100.80, 1000, "SELL"), (101.20, 2500, "BUY"), (101.50, 3500, "BUY"),
        (101.30, 800, "SELL"), (101.80, 2800, "BUY"), (102.00, 4000, "BUY"),
        (101.90, 500, "SELL"), (102.20, 3200, "BUY"), (102.50, 4500, "BUY"),
    ]
    
    for price, volume, side in demo_data:
        await asyncio.sleep(3)
        process_trade(price, volume, side)

# ========== ОСНОВНАЯ ФУНКЦИЯ ==========
async def main():
    logger.warning("=" * 50)
    logger.warning(f"🚀 T-GLASS v19.1 | {TICKER}")
    logger.warning("=" * 50)
    
    # Запуск health сервера
    await start_health_server()
    
    # Запуск симуляции
    asyncio.create_task(simulate_trades())
    
    # Основной цикл
    counter = 0
    while True:
        await asyncio.sleep(60)
        counter += 1
        uptime = int(time.time() - stats.start)
        logger.info(f"💓 Heartbeat #{counter} | Uptime: {uptime}s | Trades: {stats.trades} | Δ={stats.delta:+,} | Signals: {stats.alerts}")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("🛑 Shutting down...")
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        sys.exit(1)