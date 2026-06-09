#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import asyncio
import logging
from datetime import datetime

logger = logging.getLogger('commands')


class CommandHandler:
    """Обработчик команд для MAX Bot"""
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
        """Запуск обработчика команд (polling)"""
        logger.info("🚀 Command handler running")
        while True:
            await asyncio.sleep(1)

    async def handle_message(self, message):
        """Обработка входящего сообщения"""
        if not message.text:
            return
        if message.from_user.id != self.allowed_chat_id:
            logger.warning(f"Unauthorized access from {message.from_user.id}")
            return

        text = message.text.strip()
        logger.info(f"📨 Command received: {text}")

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
        """Отправка сообщения"""
        try:
            await self.bot.send_message(user_id=self.allowed_chat_id, text=text)
        except Exception as e:
            logger.error(f"Send error: {e}")

    async def _cmd_status(self):
        """Команда /status"""
        if not self.stats:
            await self._send("❌ Статистика недоступна")
            return

        rt = int(datetime.now().timestamp() - self.stats.start)
        text = f"""📊 **T-GLASS STATUS**

🟢 Бот: {'Активен' if not self.paused else '⏸️ Пауза'}
🧠 AI режим: {self.ai_mode.upper()}
🎯 Score порог: {self.config.SETUP_SCORE_REQUIRED if self.config else 40}

📈 Статистика:
• Время работы: {rt // 3600}ч {(rt % 3600) // 60}м
• Сделок: {self.stats.trades}
• Сигналов: {self.stats.alerts}
• Дельта: {self.stats.delta:+,}

💰 Затраты AI: ${getattr(self.stats, 'total_cost', 0):.6f}

/help - все команды"""
        await self._send(text)

    async def _cmd_settings(self):
        """Команда /settings"""
        if not self.config:
            await self._send("❌ Конфигурация недоступна")
            return

        text = f"""⚙️ **НАСТРОЙКИ**

**Пороги:**
• SETUP_SCORE_REQUIRED: {self.config.SETUP_SCORE_REQUIRED}
• AI_CONFIDENCE_REQUIRED: {self.config.AI_CONFIDENCE_REQUIRED}%
• DELTA_THRESHOLD: {self.config.DELTA_THRESHOLD:,}
• TAPE_SPEED_THRESHOLD: {self.config.TAPE_SPEED_THRESHOLD}

**AI:**
• Модель: {self.config.VSEGPT_MODEL}
• Cooldown: {self.config.AI_COOLDOWN_SECONDS}с
• Режим: {self.ai_mode.upper()}

/ai_mode [full|fallback] - смена режима AI"""
        await self._send(text)

    async def _cmd_ai_mode(self, mode=None):
        """Команда /ai_mode"""
        if mode:
            if mode.lower() in ['full', 'fallback']:
                self.ai_mode = mode.lower()
                if self.ai_analyzer:
                    self.ai_analyzer.set_mode(self.ai_mode)
                await self._send(f"🧠 AI режим изменён: {self.ai_mode.upper()}")
            else:
                await self._send(f"❌ Неверный режим. Используйте: full или fallback")
        else:
            await self._send(f"🧠 Текущий AI режим: {self.ai_mode.upper()}\n\n"
                            f"full - полный AI анализ\n"
                            f"fallback - только детекторы (экономия)\n\n"
                            f"/ai_mode [full|fallback]")

    async def _cmd_stats(self):
        """Команда /stats (детальная статистика)"""
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
• AI NO: {self.stats.ai_no}

**AI:**
• Режим: {self.ai_mode.upper()}
• Затраты: ${getattr(self.stats, 'total_cost', 0):.6f}

/status - общий статус"""
        await self._send(text)

    async def _cmd_help(self):
        """Команда /help"""
        text = """🤖 **T-GLASS - Команды**

**Управление:**
/pause - остановить отправку сигналов
/resume - возобновить отправку

**Информация:**
/status - текущий статус бота
/stats - детальная статистика
/settings - текущие настройки

**AI:**
/ai_mode - показать текущий режим
/ai_mode full - включить полный AI
/ai_mode fallback - только детекторы

/help - эта справка

**Пороги:**
• Score ≥ 40 → вызов AI
• Confidence ≥ 80% → сигнал
• |Delta| ≥ 7000 → детектор дельты
• Cooldown 120с между AI вызовами"""
        await self._send(text)

    def is_bot_paused(self) -> bool:
        """Проверка, приостановлен ли бот"""
        return self.paused

    def get_ai_mode(self) -> str:
        """Получение текущего режима AI"""
        return self.ai_mode