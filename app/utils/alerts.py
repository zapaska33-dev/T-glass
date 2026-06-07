#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import logging

logger = logging.getLogger('alerts')

_max_bot = None
_chat_id = None


def init_max_bot(bot, chat_id: int):
    """Инициализация MAX бота"""
    global _max_bot, _chat_id
    _max_bot = bot
    _chat_id = chat_id
    logger.info(f"✅ MAX Bot initialized for chat_id={chat_id}")


async def send_alert(bot, message: str, signal_id: str = None, command_handler=None) -> bool:
    """Отправка алерта в MAX"""
    try:
        if command_handler and command_handler.is_bot_paused():
            logger.info(f"Bot paused, signal {signal_id} not sent")
            return False

        await bot.send_message(
            user_id=_chat_id,
            text=message
        )

        logger.info(f"✅ Alert sent: {signal_id}")
        return True

    except Exception as e:
        logger.error(f"Failed to send alert: {e}")
        return False