#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
VTBR ORDER FLOW DETECTOR v16.9
Fixed indentation and score from secrets
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import asyncio
import time
import logging
from collections import deque

from aiogram import Bot
from tradernet import Core, TradernetWebsocket

import config
from profiles import apply_profile, current_profile, Profile, PROFILES
from utils.logging import setup_logging
from utils.alerts import send_alert
from bot.commands import CommandHandler
from ai_analyzer import ai_analyzer

# Setup logging
logger, logger_trade, logger_ai = setup_logging()

# ============================================================
# GLOBAL STATE
# ============================================================

bot = None
core = None
command_handler = None

# Storage
recent_trades = deque(maxlen=10000)

# Stats counters
class Stats:
    def __init__(self):
        self.start_time = time.time()
        self.total_quotes = 0
        self.total_trades = 0
        self.qualified_events = 0
        self.alerts_sent = 0
        self.ai_requests = 0
        self.ai_confirmed = 0
        self.ai_rejected = 0
        self.book_updates = 0
        self.delta = 0
        self.quotes_skipped_no_volume = 0
        self.quotes_skipped_duplicate = 0

stats = Stats()

# Quote deduplication
last_trade_counter = 0
last_trade_price = 0
last_trade_volume = 0
last_trade_time = ""

# ============================================================
# QUOTE PROCESSING
# ============================================================

async def process_quote(data):
    global last_trade_counter, last_trade_price, last_trade_volume, last_trade_time
    
    try:
        stats.total_quotes += 1
        
        ltp = data.get("ltp")
        lts = data.get("lts")
        ltt = data.get("ltt")
        trade_counter = data.get("trades")
        
        if data.get("init") == 1:
            return
        
        if ltp is None:
            return
        
        if lts is None or lts == 0:
            stats.quotes_skipped_no_volume += 1
            return
        
        if trade_counter is not None:
            if trade_counter <= last_trade_counter:
                stats.quotes_skipped_duplicate += 1
                return
            last_trade_counter = trade_counter
        else:
            if (ltp == last_trade_price and 
                lts == last_trade_volume and 
                ltt == last_trade_time):
                stats.quotes_skipped_duplicate += 1
                return
        
        last_trade_price = ltp
        last_trade_volume = lts
        last_trade_time = ltt
        
        try:
            price = float(ltp)
            volume = int(lts)
        except (ValueError, TypeError):
            return
        
        if price <= 0 or volume <= 0:
            return
        
        stats.total_trades += 1
        logger.info(f"TRADE #{stats.total_trades} | Price={price:.4f} | Volume={volume:,}")
        
        await process_trade(price, volume, data)
        
    except Exception as e:
        logger.error(f"Quote error: {e}")

# ============================================================
# TRADE PROCESSING
# ============================================================

async def process_trade(price: float, volume: int, data: dict):
    global bot, command_handler
    
    recent_trades.append({
        "time": time.time(),
        "price": price,
        "volume": volume,
        "side": "UNKNOWN",
    })
    
    if volume >= config.MIN_PRINT_VOLUME:
        logger.info(f"LARGE PRINT | Price={price:.4f} | VOL={volume:,}")
        
        if bot and command_handler and not command_handler.is_bot_paused():
            await send_alert(
                bot,
                f"LARGE PRINT | Price={price:.4f} | VOL={volume:,}",
                f"large_print_{int(time.time())}",
                None
            )
    
    await check_setup_score(price, volume)

# ============================================================
# SETUP SCORE CALCULATION
# ============================================================

async def check_setup_score(price: float, volume: int):
    """Расчет setup_score и триггер AI"""
    setup_score = 0
    
    if volume >= config.MIN_PRINT_VOLUME:
        setup_score += 30
    if stats.total_trades % 10 == 0:
        setup_score += 20
    if price > 0:
        setup_score += 10
    
    # Добавляем дельту если есть
    delta = stats.delta
    if abs(delta) > config.DELTA_THRESHOLD:
        setup_score += 20
    
    logger.info(f"SETUP SCORE: {setup_score} (required: {config.SETUP_SCORE_REQUIRED})")
    
    if setup_score >= config.SETUP_SCORE_REQUIRED:
        stats.qualified_events += 1
        logger.warning(f"QUALIFIED EVENT #{stats.qualified_events} | Score={setup_score}")
        await trigger_ai(price, volume, setup_score, delta)

# ============================================================
# AI TRIGGER
# ============================================================

async def trigger_ai(price: float, volume: int, setup_score: int, delta: int):
    """Запуск AI анализа с реальным вызовом"""
    global bot, command_handler
    
    logger.warning(f"🤖 AI TRIGGERED | Score={setup_score} | Price={price:.4f} | Volume={volume:,} | Delta={delta:,}")
    
    stats.ai_requests += 1
    
    try:
        logger.warning("🌐 SENDING REQUEST TO AI")
        
        # Получаем tape speed для контекста
        tape_speed = 0
        if len(recent_trades) > 10:
            now = time.time()
            recent = [t for t in recent_trades if now - t["time"] <= 5]
            tape_speed = len(recent)
        
        ai_result = await ai_analyzer.analyze(
            price=price,
            volume=volume,
            setup_score=setup_score,
            delta=delta,
            tape_speed=tape_speed
        )
        
        logger.warning(f"✅ AI RESPONSE | Direction={ai_result.direction} | Confidence={ai_result.confidence}%")
        
    except Exception as e:
        logger.exception(f"❌ AI REQUEST FAILED: {e}")
        return
    
    # Проверка confidence
    if ai_result.confidence < config.AI_CONFIDENCE_REQUIRED:
        stats.ai_rejected += 1
        logger.info(f"⏭️ AI REJECTED | Confidence={ai_result.confidence}% < {config.AI_CONFIDENCE_REQUIRED}%")
        return
    
    if ai_result.direction == "NONE":
        stats.ai_rejected += 1
        logger.info(f"⏭️ AI REJECTED | Direction=NONE")
        return
    
    stats.ai_confirmed += 1
    stats.alerts_sent += 1
    
    tick_size = 0.005
    if ai_result.direction == "LONG":
        stop_price = price - ai_result.stop_ticks * tick_size
        target_price = price + ai_result.take_ticks * tick_size
    else:
        stop_price = price + ai_result.stop_ticks * tick_size
        target_price = price - ai_result.take_ticks * tick_size
    
    # Красивое сообщение на русском
    if bot and command_handler and not command_handler.is_bot_paused():
        alert_message = (
            f"🚨 **AI СИГНАЛ**\n\n"
            f"📊 **Направление:** {ai_result.direction}\n"
            f"🎯 **Уверенность:** {ai_result.confidence}%\n"
            f"📈 **Оценка сетапа:** {setup_score}\n\n"
            f"💰 **Вход:** {price:.4f} RUB\n"
            f"🛑 **Стоп:** {stop_price:.4f} ({ai_result.stop_ticks} тиков)\n"
            f"🎯 **Цель:** {target_price:.4f} ({ai_result.take_ticks} тиков)\n"
            f"📐 **Risk/Reward:** {ai_result.take_ticks / ai_result.stop_ticks:.1f}\n\n"
            f"📝 **Обоснование:**\n{ai_result.reason}\n\n"
            f"📊 **Контекст:**\n"
            f"   • Объем: {volume:,}\n"
            f"   • Дельта 1м: {delta:+,}\n"
            f"   • Оценка: {setup_score}"
        )
        
        await send_alert(bot, alert_message, f"signal_{int(time.time())}", None)
        logger.warning(f"📤 AI SIGNAL SENT | Direction={ai_result.direction} | Confidence={ai_result.confidence}%")

# ============================================================
# WEBSOCKET STREAMS
# ============================================================

async def websocket_loop():
    global core
    
    logger.info(f"Using ticker: [{config.TICKER}]")
    
    while True:
        try:
            async with TradernetWebsocket(core) as ws:
                logger.info(f"WebSocket connected for {config.TICKER}")
                
                async def handle_quotes():
                    async for data in ws.quotes(config.TICKER):
                        if data:
                            await process_quote(data)
                
                async def handle_orderbook():
                    async for data in ws.market_depth(config.TICKER):
                        if data:
                            stats.book_updates += 1
                
                await asyncio.gather(handle_quotes(), handle_orderbook())
                
        except Exception as e:
            logger.error(f"WebSocket error: {e}, reconnecting in 5s")
            await asyncio.sleep(5)

# ============================================================
# STATS LOOP
# ============================================================

async def stats_loop():
    while True:
        await asyncio.sleep(60)
        runtime = int(time.time() - stats.start_time)
        logger.info(
            f"📊 STATS | Runtime={runtime}s | "
            f"Trades={stats.total_trades} | "
            f"Qualified={stats.qualified_events} | "
            f"Alerts={stats.alerts_sent} | "
            f"AI Requests={stats.ai_requests} | "
            f"AI Confirmed={stats.ai_confirmed} | "
            f"AI Rejected={stats.ai_rejected}"
        )

# ============================================================
# HEALTH CHECK
# ============================================================

async def health_server():
    try:
        from aiohttp import web
        
        async def health(request):
            return web.json_response({
                "status": "ok",
                "ticker": config.TICKER,
                "uptime": int(time.time() - stats.start_time),
                "trades": stats.total_trades,
                "alerts": stats.alerts_sent,
                "threshold": config.SETUP_SCORE_REQUIRED,
                "profile": current_profile
            })
        
        app = web.Application()
        app.router.add_get("/health", health)
        runner = web.AppRunner(app)
        await runner.setup()
        site = web.TCPSite(runner, "0.0.0.0", 80)
        await site.start()
        logger.info("Health check on port 80")
        await asyncio.Event().wait()
    except Exception as e:
        logger.warning(f"Health check error: {e}")

# ============================================================
# SELF TEST
# ============================================================

async def run_self_test():
    logger.info("=" * 60)
    logger.info("🔍 RUNNING SELF-TEST...")
    logger.info("=" * 60)
    
    if config.PUBLIC_KEY and config.PRIVATE_KEY:
        logger.info("  ✅ Core API Keys: OK")
    else:
        logger.error("  ❌ Core API Keys: MISSING")
    
    if config.TELEGRAM_TOKEN and config.TELEGRAM_CHAT_ID:
        logger.info("  ✅ Telegram Config: OK")
    else:
        logger.error("  ❌ Telegram Config: MISSING")
    
    logger.info("=" * 60)
    logger.info(f"📊 TICKER: {config.TICKER}")
    logger.info(f"📊 Type: {'FUTURES' if config.IS_FUTURES else 'STOCK'}")
    logger.info("=" * 60)
    logger.info("✅ SELF-TEST COMPLETE")
    logger.info("=" * 60)

async def send_startup_report():
    setup_score_value = config.SETUP_SCORE_REQUIRED
    setup_score_source = os.environ.get("SETUP_SCORE_REQUIRED", "DEFAULT")
    
    message = f"""🤖 **VTBR ORDER FLOW DETECTOR v16.9**

📊 Ticker: {config.TICKER}
📊 Type: {'FUTURES' if config.IS_FUTURES else 'STOCK'}
🎯 AI Threshold: {setup_score_value}
📦 Source: {setup_score_source}
🧠 AI Model: {config.VSEGPT_MODEL}

✅ Fixed indentation
✅ Score from secrets

📱 Commands: /pause, /resume, /status, /help, /threshold"""
    return message

# ============================================================
# MAIN
# ============================================================

async def main():
    global bot, core, command_handler
    
    stats.start_time = time.time()
    
    # Отладка: показываем откуда берется SETUP_SCORE_REQUIRED
    logger.warning(f"🔍 SETUP_SCORE_REQUIRED from env: {os.environ.get('SETUP_SCORE_REQUIRED', 'NOT SET')}")
    logger.warning(f"🔍 SETUP_SCORE_REQUIRED from config: {config.SETUP_SCORE_REQUIRED}")
    
    logger.info("=" * 60)
    logger.info("🚀 VTBR ORDER FLOW DETECTOR v16.9")
    logger.info(f"📊 TICKER: {config.TICKER}")
    logger.info("=" * 60)
    
    logger.info("=" * 50)
    logger.info("📊 CONFIGURATION")
    logger.info("=" * 50)
    
    setup_score_value = config.SETUP_SCORE_REQUIRED
    setup_score_source = os.environ.get("SETUP_SCORE_REQUIRED", "DEFAULT")
    
    logger.info(f"   SETUP_SCORE_REQUIRED: {setup_score_value} (порог для AI)")
    logger.info(f"      📦 Source: {setup_score_source}")
    logger.info(f"   AI_CONFIDENCE_REQUIRED: {config.AI_CONFIDENCE_REQUIRED}%")
    logger.info(f"   AI_COOLDOWN_SECONDS: {config.AI_COOLDOWN_SECONDS}s")
    logger.info(f"   AI_MODEL: {config.VSEGPT_MODEL}")
    logger.info("=" * 50)
    
    try:
        core = Core(config.PUBLIC_KEY, config.PRIVATE_KEY)
        logger.info("✅ Core initialized")
    except Exception as e:
        logger.error(f"❌ Core init failed: {e}")
        raise
    
    try:
        bot = Bot(token=config.TELEGRAM_TOKEN)
        logger.info("✅ Telegram bot initialized")
    except Exception as e:
        logger.error(f"❌ Telegram init failed: {e}")
        raise
    
    await run_self_test()
    apply_profile(Profile.PRODUCTION)
    
    try:
        startup_message = await send_startup_report()
        await bot.send_message(config.TELEGRAM_CHAT_ID, startup_message)
        logger.info("✅ Startup report sent")
        
        await bot.send_message(
            config.TELEGRAM_CHAT_ID,
            f"🟢 **VTBR DETECTOR ONLINE v16.9**\n\n"
            f"📊 Ticker: {config.TICKER}\n"
            f"🎯 AI Threshold: {setup_score_value}\n"
            f"🧠 AI Model: {config.VSEGPT_MODEL}\n\n"
            f"📱 Commands: /pause, /resume, /status, /help, /threshold"
        )
    except Exception as e:
        logger.error(f"Startup message failed: {e}")
    
    command_handler = CommandHandler(bot)
    asyncio.create_task(command_handler.run())
    
    await asyncio.gather(
        websocket_loop(),
        stats_loop(),
        health_server()
    )

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Shutting down...")
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        raise
