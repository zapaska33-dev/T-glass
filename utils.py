#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import logging
import os
from logging.handlers import RotatingFileHandler

_logger = None
_logger_trade = None
_logger_ai = None
_max_bot = None
_chat_id = None


def setup_logging():
    """Настройка логирования"""
    global _logger, _logger_trade, _logger_ai

    log_dir = '/data/logs'
    os.makedirs(log_dir, exist_ok=True)

    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    # Системный логгер
    _logger = logging.getLogger('tglass')
    _logger.setLevel(logging.INFO)

    file_handler = RotatingFileHandler(
        f'{log_dir}/tglass.log',
        maxBytes=10 * 1024 * 1024,
        backupCount=5
    )
    file_handler.setFormatter(formatter)
    _logger.addHandler(file_handler)

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    _logger.addHandler(console_handler)

    # Логгер трейдов
    _logger_trade = logging.getLogger('trade')
    _logger_trade.setLevel(logging.INFO)
    trade_handler = RotatingFileHandler(
        f'{log_dir}/trade.log',
        maxBytes=10 * 1024 * 1024,
        backupCount=5
    )
    trade_handler.setFormatter(formatter)
    _logger_trade.addHandler(trade_handler)

    # AI логгер
    _logger_ai = logging.getLogger('ai')
    _logger_ai.setLevel(logging.INFO)
    ai_handler = RotatingFileHandler(
        f'{log_dir}/ai.log',
        maxBytes=10 * 1024 * 1024,
        backupCount=5
    )
    ai_handler.setFormatter(formatter)
    _logger_ai.addHandler(ai_handler)

    return _logger, _logger_trade, _logger_ai


def init_max_bot(bot, chat_id):
    """Инициализация MAX бота"""
    global _max_bot, _chat_id
    _max_bot = bot
    _chat_id = chat_id
    if _logger:
        _logger.info(f"✅ MAX Bot initialized, chat_id={chat_id}")


async def send_alert(bot, message: str, signal_id: str = None, command_handler=None) -> bool:
    """Отправка алерта в MAX"""
    global _chat_id
    try:
        if command_handler and command_handler.is_bot_paused():
            if _logger:
                _logger.info(f"Bot paused, signal {signal_id} not sent")
            return False

        await bot.send_message(user_id=_chat_id, text=message)
        if _logger:
            _logger.info(f"✅ Alert sent: {signal_id}")
        return True
    except Exception as e:
        if _logger:
            _logger.error(f"Send error: {e}")
        return False