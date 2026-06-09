#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import logging
import os
from logging.handlers import RotatingFileHandler
from pathlib import Path


def setup_logging():
    """Настройка логирования с ротацией"""
    
    # Используем /data/logs для Docker
    log_dir = Path('/data/logs')
    log_dir.mkdir(parents=True, exist_ok=True)

    # Формат логов
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    # Системный логгер
    logger = logging.getLogger('tglass')
    logger.setLevel(logging.INFO)

    # Файловый handler с ротацией (10MB, 5 файлов)
    file_handler = RotatingFileHandler(
        log_dir / 'tglass.log',
        maxBytes=10 * 1024 * 1024,
        backupCount=5
    )
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    # Консольный handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # Логгер для трейдов
    logger_trade = logging.getLogger('trade')
    logger_trade.setLevel(logging.INFO)
    trade_handler = RotatingFileHandler(
        log_dir / 'trade.log',
        maxBytes=10 * 1024 * 1024,
        backupCount=5
    )
    trade_handler.setFormatter(formatter)
    logger_trade.addHandler(trade_handler)

    # AI логгер
    logger_ai = logging.getLogger('ai')
    logger_ai.setLevel(logging.INFO)
    ai_handler = RotatingFileHandler(
        log_dir / 'ai.log',
        maxBytes=10 * 1024 * 1024,
        backupCount=5
    )
    ai_handler.setFormatter(formatter)
    logger_ai.addHandler(ai_handler)

    return logger, logger_trade, logger_ai