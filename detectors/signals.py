#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import time
from enum import Enum
from dataclasses import dataclass
from typing import Dict, List, Optional


class SignalType(Enum):
    """Типы сигналов детекторов"""
    ABSORPTION = "absorption"
    PRICE_RESPONSE = "price_response"
    ICEBERG = "iceberg"
    IMBALANCE = "imbalance"
    SPOOFING = "spoofing"
    DELTA = "delta"
    WALL = "wall"
    LIQUIDITY_SHIFT = "liquidity_shift"
    TAPE_SPEED = "tape_speed"
    VOLUME_CLUSTER = "volume_cluster"
    TRADE_VELOCITY = "trade_velocity"


# Веса детекторов (обновленные для Т-Технологий)
WEIGHTS = {
    SignalType.DELTA: 35,              # Поток объема
    SignalType.SPOOFING: 30,           # Ложные заявки (разворотный)
    SignalType.ABSORPTION: 25,         # Поглощение объемов
    SignalType.PRICE_RESPONSE: 20,     # Ценовая реакция
    SignalType.ICEBERG: 20,            # Айсберг-заявки (накопительный)
    SignalType.IMBALANCE: 15,          # Дисбаланс стакана
    SignalType.WALL: 15,               # Крупные стены
    SignalType.VOLUME_CLUSTER: 15,     # Кластер объемов
    SignalType.LIQUIDITY_SHIFT: 10,    # Сдвиг ликвидности
    SignalType.TAPE_SPEED: 10,         # Скорость ленты
    SignalType.TRADE_VELOCITY: 10,     # Скорость сделок
}

MAX_SCORE = sum(WEIGHTS.values())  # = 205

# TTL для детекторов (секунды)
TTL_CONFIG = {
    SignalType.ABSORPTION: 10,
    SignalType.PRICE_RESPONSE: 15,
    SignalType.ICEBERG: 20,
    SignalType.IMBALANCE: 5,
    SignalType.SPOOFING: 8,
    SignalType.DELTA: 30,
    SignalType.WALL: 10,
    SignalType.LIQUIDITY_SHIFT: 5,
    SignalType.TAPE_SPEED: 3,
    SignalType.VOLUME_CLUSTER: 10,
    SignalType.TRADE_VELOCITY: 3,
}


@dataclass
class DetectorRecord:
    """Запись о срабатывании детектора"""
    detected: bool = False
    value: Optional[Dict] = None
    details: str = ""
    direction: str = ""
    timestamp: float = 0


class DetectorJournal:
    """Журнал детекторов с TTL"""
    
    def __init__(self):
        self.detectors: Dict[SignalType, DetectorRecord] = {}
        self.bias: float = 0.0

    def set(self, signal_type: SignalType, value: Dict, details: str, direction: str):
        """Установка детектора"""
        self.detectors[signal_type] = DetectorRecord(
            detected=True,
            value=value,
            details=details,
            direction=direction,
            timestamp=time.time()
        )

    def get_components(self) -> Dict:
        """Получение активных компонентов"""
        now = time.time()
        components = {}
        for st, rec in self.detectors.items():
            ttl = TTL_CONFIG.get(st, 10)
            if rec.detected and now - rec.timestamp < ttl:
                components[st.value] = {
                    "details": rec.details,
                    "direction": rec.direction,
                    "weight": WEIGHTS.get(st, 10)
                }
        return components

    def get_signals(self) -> List[str]:
        """Получение списка активных сигналов"""
        now = time.time()
        signals = []
        for st, rec in self.detectors.items():
            ttl = TTL_CONFIG.get(st, 10)
            if rec.detected and now - rec.timestamp < ttl:
                signals.append(f"{st.value}:{rec.direction}")
        return signals

    def calc(self, delta: float) -> int:
        """Расчет суммарного веса и смещения (bias)"""
        total = 0
        bullish = 0
        bearish = 0
        now = time.time()

        for st, rec in self.detectors.items():
            ttl = TTL_CONFIG.get(st, 10)
            if rec.detected and now - rec.timestamp < ttl:
                weight = WEIGHTS.get(st, 10)
                total += weight
                if rec.direction == "BULLISH":
                    bullish += weight
                elif rec.direction == "BEARISH":
                    bearish += weight

        # Расчет bias в процентах
        self.bias = (bullish - bearish) / max(total, 1) * 100 if total > 0 else 0
        return total
    
    def get_detailed_score(self) -> Dict:
        """Получение детальной разбивки по весам"""
        now = time.time()
        result = {
            "total": 0,
            "bullish": 0,
            "bearish": 0,
            "components": []
        }
        
        for st, rec in self.detectors.items():
            ttl = TTL_CONFIG.get(st, 10)
            if rec.detected and now - rec.timestamp < ttl:
                weight = WEIGHTS.get(st, 10)
                result["total"] += weight
                if rec.direction == "BULLISH":
                    result["bullish"] += weight
                elif rec.direction == "BEARISH":
                    result["bearish"] += weight
                
                result["components"].append({
                    "type": st.value,
                    "weight": weight,
                    "direction": rec.direction,
                    "details": rec.details
                })
        
        return result