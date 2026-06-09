#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import time
import config
from detectors.signals import SignalType


class IcebergDetector:
    """
    Накопительный детектор айсберг-заявок для Т-Технологий.
    Отслеживает повторяющиеся сделки на одном ценовом уровне.
    """
    
    def __init__(self):
        # Структура для хранения уровней
        # key: f"{side}:{price:.2f}"
        self.levels = {}

    def detect(self, price: float, volume: int, side: str, journal, logger) -> bool:
        """
        Детектирование айсберга по накоплению объема на одном уровне.
        
        Args:
            price: цена сделки
            volume: объем сделки
            side: сторона (BUY/SELL)
            journal: журнал детекторов
            logger: логгер
        
        Returns:
            bool: True если айсберг обнаружен
        """
        now = time.time()
        
        # Формируем ключ для уровня (округляем цену до 2 знаков)
        key = f"{side}:{price:.2f}"
        
        # Создаем новый уровень если его нет
        if key not in self.levels:
            self.levels[key] = {
                "volume": 0,      # накопленный объем
                "trades": 0,      # количество сделок
                "first": now,     # время первой сделки
                "last": now,      # время последней сделки
                "alerted": False  # был ли уже сигнал
            }
        
        lvl = self.levels[key]
        
        # Накопление
        lvl["volume"] += volume
        lvl["trades"] += 1
        lvl["last"] = now
        
        # Очистка старых уровней (старше 30 секунд)
        for k in list(self.levels.keys()):
            if now - self.levels[k]["last"] > 30:
                del self.levels[k]
        
        # Пороговые значения из конфига
        min_volume = getattr(config, 'ICEBERG_TOTAL_VOLUME', 3000)
        min_trades = getattr(config, 'ICEBERG_MIN_TRADES', 8)
        
        # Проверка условий для сигнала
        if (not lvl["alerted"] 
            and lvl["volume"] >= min_volume 
            and lvl["trades"] >= min_trades):
            
            lvl["alerted"] = True
            
            # Направление сигнала
            direction = "BULLISH" if side == "BUY" else "BEARISH"
            
            # Устанавливаем сигнал в журнал
            journal.set(
                SignalType.ICEBERG,
                {
                    "price": price,
                    "volume": lvl["volume"],
                    "trades": lvl["trades"],
                    "duration": lvl["last"] - lvl["first"]
                },
                f"{side} {price:.2f} vol={lvl['volume']} n={lvl['trades']}",
                direction
            )
            
            logger.warning(
                f"🧊 ICEBERG {side} {price:.2f} | "
                f"total_vol={lvl['volume']} | "
                f"trades={lvl['trades']} | "
                f"duration={lvl['last'] - lvl['first']:.1f}s"
            )
            
            return True
        
        return False
    
    def get_stats(self) -> dict:
        """Получить статистику активных уровней"""
        return {
            "active_levels": len(self.levels),
            "levels": list(self.levels.keys())
        }
    
    def clear_old_levels(self, max_age: int = 30):
        """Принудительная очистка старых уровней"""
        now = time.time()
        for k in list(self.levels.keys()):
            if now - self.levels[k]["last"] > max_age:
                del self.levels[k]