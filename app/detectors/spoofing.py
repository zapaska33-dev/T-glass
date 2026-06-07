#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from typing import Dict
import config


class SpoofDetector:
    def __init__(self):
        self.last_bids: Dict[float, int] = {}
        self.last_asks: Dict[float, int] = {}

    def detect(self, prev_bids: Dict, prev_asks: Dict,
               curr_bids: Dict, curr_asks: Dict,
               journal, logger) -> bool:
        """Детектирование спуфинга"""
        detected = False
        thr = getattr(config, 'SPOOF_SIZE_THRESHOLD', 3000)

        # Проверяем крупные заявки, которые исчезли
        for price, size in prev_bids.items():
            if size >= thr and price not in curr_bids:
                journal.set(
                    SignalType.SPOOFING,
                    {"side": "BID", "price": price, "size": size},
                    f"BID {price:.4f} removed",
                    "BEARISH"
                )
                detected = True
                logger.warning(f"🎭 SPOOF BID")

        for price, size in prev_asks.items():
            if size >= thr and price not in curr_asks:
                journal.set(
                    SignalType.SPOOFING,
                    {"side": "ASK", "price": price, "size": size},
                    f"ASK {price:.4f} removed",
                    "BULLISH"
                )
                detected = True
                logger.warning(f"🎭 SPOOF ASK")

        return detected


# Импорт после определения класса
from .signals import SignalType