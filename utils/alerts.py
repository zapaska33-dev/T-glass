#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
MAX Alerts - отправка сигналов через MAX Bot
"""

import asyncio
import logging
from typing import Optional

from maxapi import Bot

logger = logging.getLogger('max_alerts')

# Глобальная переменная для хранения бота
_max_bot: Optional[Bot] = None
_chat_id: Optional[int] = None

def init_max_bot(bot: Bot, chat_id: int):
    """Инициализация MAX бота"""
    global _max_bot, _chat_id
    _max_bot = bot
    _chat_id = chat_id
    logger.info(f"✅ MAX Bot initialized for chat_id={chat_id}")

async def send_alert(bot, message: str, signal_id: str = None, command_handler=None) -> bool:
    """
    Отправка алерта в MAX
    
    Args:
        bot: MAX Bot instance
        message: Текст сообщения
        signal_id: ID сигнала (для дедупликации)
        command_handler: обработчик команд (для проверки паузы)
    
    Returns:
        bool: успешность отправки
    """
    try:
        # Проверяем паузу
        if command_handler and command_handler.is_bot_paused():
            logger.info(f"Bot paused, signal {signal_id} not sent")
            return False
        
        # Отправляем сообщение
        await bot.send_message(
            user_id=_chat_id,
            text=message
        )
        
        logger.info(f"✅ Alert sent to MAX: {signal_id}")
        return True
        
    except Exception as e:
        logger.error(f"❌ Failed to send MAX alert: {e}")
        return False

async def send_status(bot, status_text: str) -> bool:
    """Отправка статусного сообщения"""
    try:
        await bot.send_message(
            user_id=_chat_id,
            text=status_text
        )
        return True
    except Exception as e:
        logger.error(f"Failed to send status: {e}")
        return False

def get_max_bot() -> Optional[Bot]:
    """Получение глобального экземпляра MAX бота"""
    return _max_bot