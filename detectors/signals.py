#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import time
from dataclasses import dataclass
from typing import Dict, List, Optional

# Веса детекторов (сумма = 150)
WEIGHTS = {
    "DELTA": 40,
    "SPOOFING": 30,
    "ABSORPTION": 10,
    "PRICE_RESPONSE": 15,
    "ICEBERG": 5,
    "IMBALANCE": 10,
    "WALL": 15,
    "LIQUIDITY_SHIFT": 8,
    "TAPE_SPEED": 5,
    "VOLUME_CLUSTER": 7,
    "TRADE_VELOCITY": 5,
}

MAX_SCORE = sum(WEIGHTS.values())  # = 150

# TTL для детекторов (секунды)
TTL_CONFIG = {
    "ABSORPTION": 10,
    "PRICE_RESPONSE": 15,
    "ICEBERG": 20,
    "IMBALANCE": 5,
    "SPOOFING": 8,
    "DELTA": 30,
    "WALL": 10,
    "LIQUIDITY_SHIFT": 5,
    "TAPE_SPEED": 3,
    "VOLUME_CLUSTER": 10,
    "TRADE_VELOCITY": 3,
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
        self.detectors: Dict[str, DetectorRecord] = {}
        self.bias: float = 0.0

    def set(self, signal_type: str, value: Dict, details: str, direction: str):
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
                components[st] = {
                    "details": rec.details,
                    "direction": rec.direction
                }
        return components

    def get_signals(self) -> List[str]:
        """Получение списка активных сигналов"""
        now = time.time()
        signals = []
        for st, rec in self.detectors.items():
            ttl = TTL_CONFIG.get(st, 10)
            if rec.detected and now - rec.timestamp < ttl:
                signals.append(f"{st}:{rec.direction}")
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