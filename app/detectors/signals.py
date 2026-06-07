#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from enum import Enum
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from collections import defaultdict
import time


class SignalType(Enum):
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


# Веса детекторов
WEIGHTS = {
    SignalType.DELTA: 40,
    SignalType.SPOOFING: 30,
    SignalType.ABSORPTION: 10,
    SignalType.PRICE_RESPONSE: 15,
    SignalType.ICEBERG: 5,
    SignalType.IMBALANCE: 10,
    SignalType.WALL: 15,
    SignalType.LIQUIDITY_SHIFT: 8,
    SignalType.TAPE_SPEED: 5,
    SignalType.VOLUME_CLUSTER: 7,
    SignalType.TRADE_VELOCITY: 5,
}

MAX_SCORE = sum(WEIGHTS.values())


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
    detected: bool = False
    value: Optional[Dict] = None
    details: str = ""
    direction: str = ""
    timestamp: float = 0


class DetectorJournal:
    def __init__(self):
        self.detectors: Dict[SignalType, DetectorRecord] = defaultdict(DetectorRecord)
        self.bias: float = 0.0
        self._last_calc_time: float = 0

    def set(self, signal_type: SignalType, value: Dict, details: str, direction: str):
        """Установка детектора"""
        self.detectors[signal_type] = DetectorRecord(
            detected=True,
            value=value,
            details=details,
            direction=direction,
            timestamp=time.time()
        )

    def get_components(self) -> Dict[str, Any]:
        """Получение активных компонентов"""
        components = {}
        now = time.time()
        for st, rec in self.detectors.items():
            if rec.detected and (now - rec.timestamp) <= TTL_CONFIG.get(st, 10):
                components[st.value] = {
                    "details": rec.details,
                    "direction": rec.direction
                }
        return components

    def get_signals(self) -> List[str]:
        """Получение списка сигналов"""
        signals = []
        now = time.time()
        for st, rec in self.detectors.items():
            if rec.detected and (now - rec.timestamp) <= TTL_CONFIG.get(st, 10):
                signals.append(f"{st.value}:{rec.direction}")
        return signals

    def calc(self, delta: float) -> int:
        """Расчет суммарного веса"""
        total = 0
        bullish = 0
        bearish = 0
        now = time.time()

        for st, rec in self.detectors.items():
            if rec.detected and (now - rec.timestamp) <= TTL_CONFIG.get(st, 10):
                weight = WEIGHTS.get(st, 0)
                total += weight
                if rec.direction == "BULLISH":
                    bullish += weight
                elif rec.direction == "BEARISH":
                    bearish += weight

        self.bias = (bullish - bearish) / max(total, 1) * 100 if total > 0 else 0
        return total

    def clear_expired(self):
        """Очистка просроченных детекторов"""
        now = time.time()
        expired = []
        for st, rec in self.detectors.items():
            if rec.detected and (now - rec.timestamp) > TTL_CONFIG.get(st, 10):
                expired.append(st)
        for st in expired:
            del self.detectors[st]