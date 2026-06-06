#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
MAX Bot Command Handler for TECHSMART Detector
Альтернатива Telegram командам через MAX API
"""

import asyncio
import logging
from datetime import datetime
from typing import Optional, Dict, Any

from maxapi import Bot
from maxapi.types.message import Message

logger = logging.getLogger('max_commands')

class CommandHandler:
    """Обработчик команд для MAX Bot"""
    
    def __init__(self, bot: Bot, stats=None, config_module=None, ai_analyzer=None):
        self.bot = bot
        self.stats = stats
        self.config = config_module
        self.ai_analyzer = ai_analyzer
        self.paused = False
        self.ai_mode = "full"  # full или fallback
        self.last_status_message = None
        self.allowed_chat_id = None
        
        # Загружаем chat_id из переменных
        import os
        self.allowed_chat_id = int(os.environ.get("MAX_CHAT_ID", "0"))
        
        logger.info(f"✅ MAX Command Handler initialized, chat_id={self.allowed_chat_id}")
    
    async def run(self):
        """Запуск обработчика команд"""
        logger.info("🚀 MAX Command Handler started")
        
        # Запускаем polling для получения сообщений
        while True:
            try:
                # Получаем обновления через MAX API
                # Используем метод get_updates если он есть, или вебхук
                await self._process_commands()
                await asyncio.sleep(1)
            except Exception as e:
                logger.error(f"Command handler error: {e}")
                await asyncio.sleep(5)
    
    async def _process_commands(self):
        """Обработка входящих команд"""
        try:
            # В MAX API обычно используется webhook или polling
            # Здесь заглушка - реальная реализация зависит от MAX API
            # В production нужно использовать webhook или polling из maxapi
            pass
        except Exception as e:
            logger.error(f"Process commands error: {e}")
    
    async def handle_message(self, message: Message):
        """Обработка одного сообщения"""
        if not message.text:
            return
        
        if message.from_user.id != self.allowed_chat_id:
            logger.warning(f"Unauthorized user: {message.from_user.id}")
            await self._send_message("❌ У вас нет доступа к управлению ботом")
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
        else:
            await self._send_message(f"❌ Неизвестная команда. Введите /help для списка команд")
    
    async def _send_message(self, text: str):
        """Отправка сообщения в MAX"""
        try:
            await self.bot.send_message(
                user_id=self.allowed_chat_id,
                text=text
            )
        except Exception as e:
            logger.error(f"Send message error: {e}")
    
    async def _cmd_pause(self):
        """Пауза отправки сигналов"""
        self.paused = True
        await self._send_message("⏸️ Бот приостановлен. Сигналы не отправляются.\n/resume - возобновить работу")
        logger.warning("⏸️ Bot paused by user command")
    
    async def _cmd_resume(self):
        """Возобновление отправки сигналов"""
        self.paused = False
        await self._send_message("▶️ Бот возобновлен. Сигналы отправляются.")
        logger.warning("▶️ Bot resumed by user command")
    
    async def _cmd_status(self):
        """Статус бота"""
        if not self.stats:
            await self._send_message("❌ Статистика недоступна")
            return
        
        rt = int(datetime.now().timestamp() - self.stats.start)
        total_cost = getattr(self.stats, 'total_cost', 0)
        
        status_text = f"""📊 **TECHSMART DETECTOR STATUS**

🟢 **Бот:** {'Активен' if not self.paused else '⏸️ Приостановлен'}
🧠 **AI режим:** {self.ai_mode.upper()}
🎯 **Score порог:** {self.config.SETUP_SCORE_REQUIRED if self.config else 40}
✨ **AI уверенность:** {self.config.AI_CONFIDENCE_REQUIRED if self.config else 80}%

📈 **Статистика:**
• Время работы: {rt // 3600}ч {(rt % 3600) // 60}м
• Сделок: {self.stats.trades}
• Сигналов: {self.stats.alerts}
• AI вызовов: {self.stats.ai_req}
• AI OK: {self.stats.ai_ok}
• Дельта: {self.stats.delta:+,}

💰 **Стоимость AI:** ${total_cost:.6f}

/help - все команды"""
        
        await self._send_message(status_text)
    
    async def _cmd_settings(self):
        """Настройки"""
        if not self.config:
            await self._send_message("❌ Конфигурация недоступна")
            return
        
        settings_text = f"""⚙️ **ТЕКУЩИЕ НАСТРОЙКИ**

**Пороги:**
• SETUP_SCORE_REQUIRED: {self.config.SETUP_SCORE_REQUIRED}
• AI_CONFIDENCE_REQUIRED: {self.config.AI_CONFIDENCE_REQUIRED}%
• DELTA_THRESHOLD: {self.config.DELTA_THRESHOLD:,}
• TAPE_SPEED_THRESHOLD: {self.config.TAPE_SPEED_THRESHOLD}

**AI:**
• Модель: {self.config.VSEGPT_MODEL}
• Cooldown: {self.config.AI_COOLDOWN_SECONDS}с
• MIN_BIAS_FOR_AI: {self.config.MIN_BIAS_FOR_AI}
• Режим: {self.ai_mode.upper()}

**Детекторы:**
• MIN_PRINT_VOLUME: {self.config.MIN_PRINT_VOLUME:,}
• ICEBERG_MIN_VOLUME: {self.config.ICEBERG_MIN_VOLUME:,}
• ABSORPTION_THRESHOLD: {self.config.ABSORPTION_THRESHOLD:,}

/ai_mode [full|fallback] - смена режима AI"""
        
        await self._send_message(settings_text)
    
    async def _cmd_ai_mode(self, mode: str = None):
        """Переключение режима AI"""
        if mode:
            if mode.lower() in ['full', 'fallback']:
                old_mode = self.ai_mode
                self.ai_mode = mode.lower()
                
                if self.ai_analyzer:
                    self.ai_analyzer.set_mode(self.ai_mode)
                
                await self._send_message(f"🧠 AI режим изменён: {old_mode.upper()} → {self.ai_mode.upper()}")
                logger.warning(f"AI mode changed: {old_mode} → {self.ai_mode}")
            else:
                await self._send_message(f"❌ Неверный режим. Используйте: /ai_mode full или /ai_mode fallback")
        else:
            current = self.ai_mode.upper()
            await self._send_message(f"🧠 Текущий AI режим: {current}\n\nfull - полный AI анализ\nfallback - только детекторы (экономия бюджета)\n\nИспользуйте: /ai_mode [full|fallback]")
    
    async def _cmd_stats(self):
        """Детальная статистика"""
        if not self.stats:
            await self._send_message("❌ Статистика недоступна")
            return
        
        stats_text = f"""📈 **ДЕТАЛЬНАЯ СТАТИСТИКА**

**Сделки:**
• Всего: {self.stats.trades}
• С дубликатами: {self.stats.duplicates_skipped}
• Квалифицированных: {self.stats.qualified}

**Сигналы:**
• Отправлено: {self.stats.alerts}
• AI запросов: {self.stats.ai_req}
• AI OK: {self.stats.ai_ok}
• AI NO: {self.stats.ai_no}

**Детекторы:**
• Обновлений стакана: {self.stats.book_updates}
• Дельта: {self.stats.delta:+,}

**AI:**
• Режим: {self.ai_mode.upper()}
• Стоимость: ${getattr(self.stats, 'total_cost', 0):.6f}

/status - общий статус"""
        
        await self._send_message(stats_text)
    
    async def _cmd_help(self):
        """Справка"""
        help_text = """🤖 **TECHSMART DETECTOR - Команды**

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

**Прочее:**
/help - эта справка

**Пороги срабатывания:**
• Score ≥ 40 → вызов AI
• Confidence ≥ 80% → сигнал
• |Delta| ≥ 7000 → детектор дельты
• Cooldown 120с между AI вызовами

📊 **Текущий тикер:** TECHSMART"""
        
        await self._send_message(help_text)
    
    def is_bot_paused(self) -> bool:
        """Проверка, приостановлен ли бот"""
        return self.paused
    
    def get_ai_mode(self) -> str:
        """Получение текущего режима AI"""
        return self.ai_mode