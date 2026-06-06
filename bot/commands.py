#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import asyncio
import logging
from datetime import datetime
from typing import Optional

from maxapi import Bot
from maxapi.types.message import Message

logger = logging.getLogger('commands')


class CommandHandler:
    """Обработчик команд для MAX Bot"""

    def __init__(self, bot: Bot, stats=None, config_module=None, ai_analyzer=None):
        self.bot = bot
        self.stats = stats
        self.config = config_module
        self.ai_analyzer = ai_analyzer
        self.paused = False
        self.ai_mode = "full"
        self.allowed_chat_id = None

        import os
        self.allowed_chat_id = int(os.environ.get("MAX_CHAT_ID", "0"))

        logger.info(f"✅ MAX Command Handler initialized, chat_id={self.allowed_chat_id}")

    async def run(self):
        """Запуск обработчика команд"""
        logger.info("🚀 MAX Command Handler started")
        while True:
            try:
                await self._process_commands()
                await asyncio.sleep(1)
            except Exception as e:
                logger.error(f"Command handler error: {e}")
                await asyncio.sleep(5)

    async def _process_commands(self):
        """Обработка входящих команд"""
        try:
            # Получаем обновления через getUpdates
            from maxapi.methods import GetUpdates
            updates = await self.bot(GetUpdates(offset=-1, timeout=1))

            for update in updates:
                if update.message and update.message.text:
                    await self.handle_message(update.message)
        except Exception as e:
            pass

    async def handle_message(self, message: Message):
        """Обработка сообщения"""
        if not message.text:
            return

        if message.from_user.id != self.allowed_chat_id:
            logger.warning(f"Unauthorized user: {message.from_user.id}")
            await self._send_message("❌ У вас нет доступа")
            return

        text = message.text.strip()
        logger.info(f"📨 Received command: {text}")

        if text == "/pause":
            await self._cmd_pause()
        elif text == "/resume":
            await self._cmd_resume()
        elif text == "/status":
            await self._cmd_status()
        elif text == "/settings":
            await self._cmd_settings()
        elif text == "/ai_mode":
            await self._cmd_ai_mode()
        elif text == "/stats":
            await self._cmd_stats()
        elif text == "/help":
            await self._cmd_help()
        elif text.startswith("/ai_mode "):
            mode = text.split()[1]
            await self._cmd_ai_mode(mode)

    async def _send_message(self, text: str):
        """Отправка сообщения"""
        try:
            await self.bot.send_message(
                user_id=self.allowed_chat_id,
                text=text
            )
        except Exception as e:
            logger.error(f"Send error: {e}")

    async def _cmd_pause(self):
        self.paused = True
        await self._send_message("⏸️ Бот приостановлен. /resume - возобновить")

    async def _cmd_resume(self):
        self.paused = False
        await self._send_message("▶️ Бот возобновлен")

    async def _cmd_status(self):
        if not self.stats:
            await self._send_message("❌ Статистика недоступна")
            return

        rt = int(datetime.now().timestamp() - self.stats.start)
        text = f"""📊 **T-GLASS STATUS**

🟢 Бот: {'Активен' if not self.paused else '⏸️ Пауза'}
🧠 AI: {self.ai_mode.upper()}
🎯 Score порог: {self.config.SETUP_SCORE_REQUIRED if self.config else 40}

📈 Статистика:
• Время: {rt // 3600}ч {(rt % 3600) // 60}м
• Сделок: {self.stats.trades}
• Сигналов: {self.stats.alerts}
• Дельта: {self.stats.delta:+,}

💰 Cost: ${getattr(self.stats, 'total_cost', 0):.6f}

/help - все команды"""
        await self._send_message(text)

    async def _cmd_settings(self):
        if not self.config:
            await self._send_message("❌ Конфигурация недоступна")
            return

        text = f"""⚙️ **НАСТРОЙКИ**

**Пороги:**
• SCORE: {self.config.SETUP_SCORE_REQUIRED}
• AI уверенность: {self.config.AI_CONFIDENCE_REQUIRED}%
• DELTA: {self.config.DELTA_THRESHOLD:,}
• TAPE SPEED: {self.config.TAPE_SPEED_THRESHOLD}

**AI:**
• Модель: {self.config.VSEGPT_MODEL}
• Cooldown: {self.config.AI_COOLDOWN_SECONDS}с
• Режим: {self.ai_mode.upper()}

/ai_mode [full|fallback] - смена режима"""
        await self._send_message(text)

    async def _cmd_ai_mode(self, mode=None):
        if mode:
            if mode.lower() in ['full', 'fallback']:
                self.ai_mode = mode.lower()
                if self.ai_analyzer:
                    self.ai_analyzer.set_mode(self.ai_mode)
                await self._send_message(f"🧠 AI режим: {self.ai_mode.upper()}")
        else:
            await self._send_message(f"🧠 AI режим: {self.ai_mode.upper()}\n/ai_mode full - полный\n/ai_mode fallback - эконом")

    async def _cmd_stats(self):
        if not self.stats:
            await self._send_message("❌ Статистика недоступна")
            return

        text = f"""📈 **ДЕТАЛЬНАЯ СТАТИСТИКА**

**Сделки:**
• Всего: {self.stats.trades}
• Дубликатов: {self.stats.duplicates_skipped}
• Квалифицированных: {self.stats.qualified}

**Сигналы:**
• Отправлено: {self.stats.alerts}
• AI OK: {self.stats.ai_ok}
• AI NO: {self.stats.ai_no}

**AI:**
• Режим: {self.ai_mode.upper()}
• Стоимость: ${getattr(self.stats, 'total_cost', 0):.6f}

/status - общий статус"""
        await self._send_message(text)

    async def _cmd_help(self):
        text = """🤖 **T-GLASS - Команды**

**Управление:**
/pause - пауза
/resume - возобновить

**Информация:**
/status - статус
/stats - статистика
/settings - настройки

**AI:**
/ai_mode - текущий режим
/ai_mode full - полный AI
/ai_mode fallback - эконом

/help - эта справка"""
        await self._send_message(text)

    def is_bot_paused(self) -> bool:
        return self.paused

    def get_ai_mode(self) -> str:
        return self.ai_mode