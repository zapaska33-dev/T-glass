#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import asyncio
import logging
from datetime import datetime

logger = logging.getLogger('commands')


class CommandHandler:
    def __init__(self, bot, stats=None, config_module=None, ai_analyzer=None):
        self.bot = bot
        self.stats = stats
        self.config = config_module
        self.ai_analyzer = ai_analyzer
        self.paused = False
        self.ai_mode = "full"

        import os
        self.allowed_chat_id = int(os.environ.get("MAX_CHAT_ID", "0"))
        logger.info(f"✅ CommandHandler initialized, chat_id={self.allowed_chat_id}")

    async def run(self):
        logger.info("🚀 Command handler running")
        while True:
            try:
                await asyncio.sleep(1)
            except Exception as e:
                logger.error(f"Command handler error: {e}")
                await asyncio.sleep(5)

    async def handle_message(self, message):
        if not message.text:
            return
        if message.from_user.id != self.allowed_chat_id:
            return

        text = message.text.strip()
        logger.info(f"📨 Command: {text}")

        if text == "/pause":
            self.paused = True
            await self._send("⏸️ Бот приостановлен. /resume - возобновить")
        elif text == "/resume":
            self.paused = False
            await self._send("▶️ Бот возобновлен")
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

    async def _send(self, text: str):
        try:
            await self.bot.send_message(user_id=self.allowed_chat_id, text=text)
        except Exception as e:
            logger.error(f"Send error: {e}")

    async def _cmd_status(self):
        if not self.stats:
            await self._send("❌ Статистика недоступна")
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
        await self._send(text)

    async def _cmd_settings(self):
        if not self.config:
            await self._send("❌ Конфигурация недоступна")
            return
        text = f"""⚙️ **НАСТРОЙКИ**

**Пороги:**
• SCORE: {self.config.SETUP_SCORE_REQUIRED}
• AI уверенность: {self.config.AI_CONFIDENCE_REQUIRED}%
• DELTA: {self.config.DELTA_THRESHOLD}

**AI:**
• Модель: {self.config.VSEGPT_MODEL}
• Cooldown: {self.config.AI_COOLDOWN_SECONDS}с
• Режим: {self.ai_mode.upper()}

/ai_mode [full|fallback]"""
        await self._send(text)

    async def _cmd_ai_mode(self, mode=None):
        if mode:
            if mode.lower() in ['full', 'fallback']:
                self.ai_mode = mode.lower()
                if self.ai_analyzer:
                    self.ai_analyzer.set_mode(self.ai_mode)
                await self._send(f"🧠 AI режим: {self.ai_mode.upper()}")
        else:
            await self._send(f"🧠 AI режим: {self.ai_mode.upper()}\n/ai_mode full - полный\n/ai_mode fallback - эконом")

    async def _cmd_stats(self):
        if not self.stats:
            await self._send("❌ Статистика недоступна")
            return
        text = f"""📈 **ДЕТАЛЬНАЯ СТАТИСТИКА**

**Сделки:**
• Всего: {self.stats.trades}
• Дубликатов: {self.stats.duplicates_skipped}
• Квалифицированных: {self.stats.qualified}

**Сигналы:**
• Отправлено: {self.stats.alerts}
• AI OK: {self.stats.ai_ok}

**AI:**
• Режим: {self.ai_mode.upper()}
• Стоимость: ${getattr(self.stats, 'total_cost', 0):.6f}

/status - общий статус"""
        await self._send(text)

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
        await self._send(text)

    def is_bot_paused(self) -> bool:
        return self.paused