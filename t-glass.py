#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
T-GLASS ORDER FLOW DETECTOR v19.1
Боевая версия с полной системой детекторов
Адаптация: Linux/ARM64, platformdirs
"""

import sys
import os
import asyncio
import time
from collections import deque

# Добавляем текущую директорию в PATH
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from maxapi import Bot
from tradernet import Core, TradernetWebsocket
import config
from utils.logging import setup_logging
from utils.alerts import send_alert, init_max_bot
from bot.commands import CommandHandler
from ai_analyzer import ai_analyzer
from detectors import (
    OrderbookProcessor, SpoofDetector, IcebergDetector,
    TapeSpeedDetector, DeltaTracker, DetectorJournal, MAX_SCORE
)

# Инициализация логов
logger, logger_trade, logger_ai = setup_logging()
logger.warning(f"🚀 T-GLASS v19.1 START | pid={os.getpid()} | ticker={config.TICKER} | arch={os.uname().machine}")

# ========== ГЛОБАЛЬНОЕ СОСТОЯНИЕ ==========
bot = None
core = None
command_handler = None
recent_trades = deque(maxlen=10000)


class Stats:
    """Статистика работы детектора"""
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
        self.duplicates_skipped = 0
        self.total_cost = 0.0


stats = Stats()
last_trade_price = 0
last_processed_trade_id = 0
last_processed_trade_price = 0
last_processed_trade_volume = 0

# Инициализация детекторов
orderbook = OrderbookProcessor(stats)
spoof_detector = SpoofDetector()
iceberg_detector = IcebergDetector()
tape_detector = TapeSpeedDetector()
delta_tracker = DeltaTracker()
global_journal = DetectorJournal()


# ========== ДЕТЕКТОРЫ ==========

def detect_absorption(j):
    """Детектор поглощения (absorption)"""
    recent = list(recent_trades)[-50:]
    if len(recent) < 20:
        return
    sell = sum(t.get("volume", 0) for t in recent if t.get("side") == "SELL")
    buy = sum(t.get("volume", 0) for t in recent if t.get("side") == "BUY")
    prices = [t.get("price", 0) for t in recent]
    move = max(prices) - min(prices) if len(prices) >= 2 else 0
    thr = getattr(config, 'ABSORPTION_THRESHOLD', 2000)
    if sell > thr and move < 0.02:
        j.set("ABSORPTION", {"type": "BUYER", "sell_vol": sell}, f"S={sell:,}", "BULLISH")
        logger.warning("🔥 ABSORPTION (buyer)")
    elif buy > thr and move < 0.02:
        j.set("ABSORPTION", {"type": "SELLER", "buy_vol": buy}, f"B={buy:,}", "BEARISH")
        logger.warning("🔥 ABSORPTION (seller)")


def detect_price_response(j):
    """Детектор ценовой реакции"""
    recent = list(recent_trades)[-100:]
    if len(recent) < 30:
        return
    sell = sum(t.get("volume", 0) for t in recent if t.get("side") == "SELL")
    buy = sum(t.get("volume", 0) for t in recent if t.get("side") == "BUY")
    prices = [t.get("price", 0) for t in recent]
    move = prices[-1] - prices[0] if len(prices) >= 2 else 0
    thr = getattr(config, 'PRICE_RESPONSE_THRESHOLD', 1000)
    if sell > thr and move >= -0.01:
        j.set("PRICE_RESPONSE", {"direction": "BULLISH", "sell_vol": sell}, f"S={sell:,}", "BULLISH")
        logger.warning("📊 PRICE_RESPONSE (bullish)")
    elif buy > thr and move <= 0.01:
        j.set("PRICE_RESPONSE", {"direction": "BEARISH", "buy_vol": buy}, f"B={buy:,}", "BEARISH")
        logger.warning("📊 PRICE_RESPONSE (bearish)")


def detect_iceberg(j, volume):
    """Детектор айсберга"""
    thr = getattr(config, 'ICEBERG_MIN_VOLUME', 500)
    if volume >= thr:
        j.set("ICEBERG", {"volume": volume}, f"V={volume:,}", "")
        logger.warning(f"🧊 ICEBERG {volume}")


def detect_imbalance(j):
    """Детектор дисбаланса стакана"""
    if orderbook.ask_size == 0:
        return
    ratio = orderbook.bid_size / orderbook.ask_size
    if ratio >= 2.0:
        j.set("IMBALANCE", {"dominant": "BID", "ratio": ratio}, f"R={ratio:.2f}", "BULLISH")
        logger.warning(f"⚖️ IMBALANCE BID (ratio={ratio:.2f})")
    elif ratio <= 0.5:
        j.set("IMBALANCE", {"dominant": "ASK", "ratio": ratio}, f"R={ratio:.2f}", "BEARISH")
        logger.warning(f"⚖️ IMBALANCE ASK (ratio={ratio:.2f})")


def detect_spoofing_wrapper(j):
    """Обертка для детектора спуфинга"""
    return spoof_detector.detect(orderbook.prev_bids, orderbook.prev_asks,
                                 orderbook.curr_bids, orderbook.curr_asks, j, logger)


def detect_delta(j):
    """Детектор дельты"""
    thr = getattr(config, 'DELTA_THRESHOLD', 7000)
    if abs(stats.delta) >= thr:
        bias_dir = "BULLISH" if stats.delta > 0 else "BEARISH"
        j.set("DELTA", {"delta": stats.delta}, f"Δ={stats.delta:+,}", bias_dir)
        logger.warning(f"📈 DELTA {stats.delta:+,}")


def detect_wall(j):
    """Детектор крупной стены"""
    sz = getattr(config, 'BIG_WALL_SIZE', 5000)
    for p, v in orderbook.curr_bids.items():
        if v >= sz:
            j.set("WALL", {"side": "BID", "price": p, "size": v}, f"BID {p:.4f} x{v}", "BULLISH")
            logger.warning(f"🧱 WALL BID {p:.4f} x{v}")
            return
    for p, v in orderbook.curr_asks.items():
        if v >= sz:
            j.set("WALL", {"side": "ASK", "price": p, "size": v}, f"ASK {p:.4f} x{v}", "BEARISH")
            logger.warning(f"🧱 WALL ASK {p:.4f} x{v}")
            return


def detect_liquidity_shift(j):
    """Детектор сдвига ликвидности"""
    if not hasattr(detect_liquidity_shift, "last_bid"):
        detect_liquidity_shift.last_bid = orderbook.bid_size
        detect_liquidity_shift.last_ask = orderbook.ask_size
        return
    bch = abs(orderbook.bid_size - detect_liquidity_shift.last_bid) / max(detect_liquidity_shift.last_bid, 1)
    ach = abs(orderbook.ask_size - detect_liquidity_shift.last_ask) / max(detect_liquidity_shift.last_ask, 1)
    detect_liquidity_shift.last_bid = orderbook.bid_size
    detect_liquidity_shift.last_ask = orderbook.ask_size
    if bch > 0.5:
        j.set("LIQUIDITY_SHIFT", {"direction": "BID_SHIFT", "change": bch},
              f"BID ch={bch*100:.0f}%", "BULLISH")
        logger.warning(f"🌊 LIQUIDITY_SHIFT BID ({bch*100:.0f}%)")
    elif ach > 0.5:
        j.set("LIQUIDITY_SHIFT", {"direction": "ASK_SHIFT", "change": ach},
              f"ASK ch={ach*100:.0f}%", "BEARISH")
        logger.warning(f"🌊 LIQUIDITY_SHIFT ASK ({ach*100:.0f}%)")


def detect_tape_speed_wrapper(j, ts):
    """Обертка для детектора скорости ленты"""
    tape_detector.update(j, logger)


def detect_volume_cluster(j):
    """Детектор кластера объемов"""
    now = time.time()
    recent = [t for t in recent_trades if now - t.get("time", 0) <= 10]
    minv = getattr(config, 'MIN_PRINT_VOLUME', 500)
    large = [t for t in recent if t.get("volume", 0) >= minv / 2]
    if len(large) >= 3:
        j.set("VOLUME_CLUSTER", {"cluster_size": len(large)}, f"{len(large)} prints", "")
        logger.warning(f"📦 VOLUME_CLUSTER ({len(large)} large trades)")


def detect_trade_velocity(j):
    """Детектор скорости сделок"""
    now = time.time()
    recent = [t for t in recent_trades if now - t.get("time", 0) <= 3]
    vel = len(recent) / 3
    thr = getattr(config, 'TAPE_SPEED_THRESHOLD', 15)
    if vel >= thr:
        j.set("TRADE_VELOCITY", {"velocity": vel}, f"{vel:.1f} t/s", "")
        logger.warning(f"🏃 TRADE_VELOCITY {vel:.1f} t/s")


# ========== ОБРАБОТКА ==========

async def process_quote(data):
    """Обработка котировки от WebSocket"""
    global last_trade_price, last_processed_trade_id
    global last_processed_trade_price, last_processed_trade_volume

    try:
        ltp = data.get("ltp")
        lts = data.get("lts")
        trade_counter = data.get("trades")

        if data.get("init") == 1 or ltp is None or lts is None or lts == 0:
            return

        price, volume = float(ltp), int(lts)
        if price <= 0 or volume <= 0:
            return

        # Защита от дублирования
        if trade_counter is not None:
            if trade_counter <= last_processed_trade_id:
                stats.duplicates_skipped += 1
                return
            last_processed_trade_id = trade_counter
        elif price == last_processed_trade_price and volume == last_processed_trade_volume:
            stats.duplicates_skipped += 1
            return

        last_processed_trade_price = price
        last_processed_trade_volume = volume

        # Определяем сторону сделки
        side = "UNKNOWN"
        if last_trade_price > 0:
            if price > last_trade_price:
                side = "BUY"
            elif price < last_trade_price:
                side = "SELL"
        last_trade_price = price

        stats.trades += 1
        logger_trade.info(f"T #{stats.trades} | price={price:.4f} vol={volume} side={side}")
        recent_trades.append({
            "time": time.time(),
            "price": price,
            "volume": volume,
            "side": side
        })

        min_delta = getattr(config, 'MIN_DELTA_VOLUME', 200)
        if volume >= min_delta:
            signed = volume if side == "BUY" else (-volume if side == "SELL" else 0)
            stats.delta = delta_tracker.update(signed)

        await check_setup(price, volume, side)
    except Exception as e:
        logger.error(f"Quote processing error: {e}")


async def check_setup(price, volume, side):
    """Проверка сетапа и вызов AI при необходимости"""
    global global_journal

    j = DetectorJournal()
    ts = time.time()

    # Запуск всех детекторов
    detect_absorption(j)
    detect_price_response(j)
    detect_iceberg(j, volume)
    detect_imbalance(j)
    detect_spoofing_wrapper(j)
    detect_delta(j)
    detect_wall(j)
    detect_liquidity_shift(j)
    detect_tape_speed_wrapper(j, ts)
    detect_volume_cluster(j)
    detect_trade_velocity(j)

    # Обновляем глобальный журнал
    for st, det in j.detectors.items():
        if det.detected:
            global_journal.set(st, det.value, det.details, det.direction)

    score = global_journal.calc(stats.delta)
    bias = global_journal.bias
    percent = int(score / MAX_SCORE * 100) if MAX_SCORE > 0 else 0

    logger.warning(f"🎯 SCORE={score}/{MAX_SCORE}({percent}%) BIAS={bias:+.2f} Δ={stats.delta:+,}")

    required = getattr(config, 'SETUP_SCORE_REQUIRED', 40)
    if score >= required:
        stats.qualified += 1
        logger_ai.info(f"🤖 AI REQUEST | score={score} bias={bias:.1f} delta={stats.delta}")

        res = await ai_analyzer.analyze(
            price, volume, score, stats.delta, 0,
            global_journal.get_components(),
            global_journal.get_signals(), bias
        )

        if hasattr(ai_analyzer, 'vsegpt_client') and ai_analyzer.vsegpt_client:
            stats.total_cost = ai_analyzer.vsegpt_client.total_cost

        if res and res.direction != "NONE":
            if res.confidence >= getattr(config, 'AI_CONFIDENCE_REQUIRED', 80):
                await send_signal(price, volume, score, stats.delta, bias, res)
            else:
                logger_ai.info(f"❌ AI SIGNAL REJECTED | confidence={res.confidence}% < {config.AI_CONFIDENCE_REQUIRED}%")


async def send_signal(price, volume, score, delta, bias, res):
    """Отправка сигнала в MAX Bot"""
    global bot, command_handler
    percent = int(score / MAX_SCORE * 100) if MAX_SCORE > 0 else 0
    stats.ai_ok += 1
    stats.alerts += 1

    tick = getattr(config, 'PRICE_TICK', 0.005)
    if res.direction == "LONG":
        stop = price - res.stop_ticks * tick
        target = price + res.take_ticks * tick
    else:
        stop = price + res.stop_ticks * tick
        target = price - res.take_ticks * tick

    msg = f"""🚨 **T-GLASS AI СИГНАЛ**

**{res.direction}** | Уверенность: **{res.confidence}%**

📊 **Параметры:**
• Оценка сетапа: {score} ({percent}%)
• Смещение (bias): {bias:+.1f}
• Дельта (delta): {delta:+,}

💹 **Уровни:**
• Вход: {price:.4f}
• Стоп: {stop:.4f}
• Цель: {target:.4f}
• Риск/Прибыль: {res.take_ticks / res.stop_ticks:.1f}

📝 **Причина:** {res.reason}

#T-GLASS #{config.TICKER}"""

    if bot and command_handler and not command_handler.is_bot_paused():
        await send_alert(bot, msg, f"signal_{int(time.time())}", command_handler)
        logger.warning(f"📤 SIGNAL SENT | {res.direction} | conf={res.confidence}%")
        logger_ai.info(f"✅ AI RESPONSE | {res.direction} | conf={res.confidence}% | {res.reason}")


# ========== WEBSOCKET ==========

async def websocket_loop():
    """WebSocket цикл с автоматическим reconnect"""
    global core
    logger.info(f"Connecting to ticker: [{config.TICKER}]")
    reconnect_delay = 1

    while True:
        try:
            async with TradernetWebsocket(core) as ws:
                logger.info(f"✅ WebSocket connected for {config.TICKER}")
                reconnect_delay = 1

                async def handle_quotes():
                    async for data in ws.quotes(config.TICKER):
                        if data:
                            await process_quote(data)

                async def handle_orderbook():
                    async for data in ws.market_depth(config.TICKER):
                        if data:
                            stats.book_updates += 1
                            bids = data.get("bids", [])
                            asks = data.get("asks", [])
                            if bids or asks:
                                orderbook.update(bids, asks, time.time())

                await asyncio.gather(handle_quotes(), handle_orderbook())

        except Exception as e:
            logger.error(f"WebSocket error: {e}, reconnecting in {reconnect_delay}s")
            await asyncio.sleep(reconnect_delay)
            reconnect_delay = min(reconnect_delay * 2, 60)


# ========== СТАТИСТИКА ==========

async def stats_loop():
    """Периодический вывод статистики"""
    while True:
        await asyncio.sleep(60)
        rt = int(time.time() - stats.start)
        logger.info(f"📊 STATS | uptime={rt}s | trades={stats.trades} | book={stats.book_updates} | "
                    f"delta={stats.delta:+,} | qualified={stats.qualified} | alerts={stats.alerts} | "
                    f"ai_ok={stats.ai_ok} ai_no={stats.ai_no} | dup={stats.duplicates_skipped} | "
                    f"cost=${stats.total_cost:.6f}")


# ========== HEALTH CHECK ==========

async def health_server():
    """Health check сервер для мониторинга"""
    try:
        from aiohttp import web

        async def health(request):
            return web.json_response({
                "status": "ok",
                "version": "19.1",
                "name": "T-GLASS",
                "ticker": config.TICKER,
                "arch": os.uname().machine,
                "trades": stats.trades,
                "delta": stats.delta,
                "alerts": stats.alerts,
                "uptime": time.time() - stats.start
            })

        app = web.Application()
        app.router.add_get("/health", health)
        app.router.add_get("/", health)

        runner = web.AppRunner(app)
        await runner.setup()
        site = web.TCPSite(runner, "0.0.0.0", 80)
        await site.start()

        logger.info("🏥 Health check: http://0.0.0.0:80/health")
        await asyncio.Event().wait()
    except Exception as e:
        logger.error(f"Health server error: {e}")


# ========== MAIN ==========

async def main():
    """Главная функция"""
    global bot, core, command_handler, global_journal

    logger.warning("=" * 50)
    logger.warning(f"🚀 T-GLASS v19.1 | {config.TICKER} | SCORE={getattr(config, 'SETUP_SCORE_REQUIRED', 40)}")
    logger.warning(f"   Arch: {os.uname().machine} | Platform: {sys.platform}")
    logger.warning("=" * 50)

    global_journal = DetectorJournal()

    # Инициализация TraderNet Core
    try:
        core = Core(config.PUBLIC_KEY, config.PRIVATE_KEY)
        logger.info("✅ TraderNet Core initialized")
    except Exception as e:
        logger.error(f"❌ Core init failed: {e}")
        raise

    # Инициализация MAX Bot
    try:
        bot = Bot(token=config.MAX_BOT_TOKEN)
        logger.info("✅ MAX Bot initialized")
        chat_id = int(os.environ.get("MAX_CHAT_ID", "0"))
        init_max_bot(bot, chat_id)
    except Exception as e:
        logger.error(f"❌ MAX Bot init failed: {e}")
        raise

    # Инициализация обработчика команд
    command_handler = CommandHandler(bot, stats, config, ai_analyzer)
    asyncio.create_task(command_handler.run())
    logger.info("✅ Command handler started")

    # Отправка приветственного сообщения
    try:
        await bot.send_message(
            user_id=int(os.environ.get("MAX_CHAT_ID", "0")),
            text=f"🟢 **T-GLASS v19.1**\n"
                 f"📊 Тикер: {config.TICKER}\n"
                 f"🎯 Score порог: {getattr(config, 'SETUP_SCORE_REQUIRED', 40)}\n"
                 f"🧠 AI режим: FULL\n"
                 f"💻 Arch: {os.uname().machine}\n\n"
                 f"📝 /help - список команд"
        )
        logger.info("✅ Welcome message sent")
    except Exception as e:
        logger.error(f"Welcome message error: {e}")

    # Запуск всех циклов
    await asyncio.gather(
        websocket_loop(),
        stats_loop(),
        health_server()
    )


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("🛑 Shutting down by user...")
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        sys.exit(1)