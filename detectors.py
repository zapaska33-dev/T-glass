#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import time
from collections import deque
from dataclasses import dataclass
from typing import Dict, List, Tuple, Optional

import config

MAX_SCORE = 150


@dataclass
class DetectorRecord:
    detected: bool = False
    value: Optional[Dict] = None
    details: str = ""
    direction: str = ""
    timestamp: float = 0


class DetectorJournal:
    def __init__(self):
        self.detectors: Dict[str, DetectorRecord] = {}
        self.bias: float = 0.0

    def set(self, signal_type: str, value: Dict, details: str, direction: str):
        self.detectors[signal_type] = DetectorRecord(
            detected=True,
            value=value,
            details=details,
            direction=direction,
            timestamp=time.time()
        )

    def get_components(self) -> Dict:
        now = time.time()
        components = {}
        for st, rec in self.detectors.items():
            if rec.detected and now - rec.timestamp < 10:
                components[st] = {"details": rec.details, "direction": rec.direction}
        return components

    def get_signals(self) -> List[str]:
        now = time.time()
        signals = []
        for st, rec in self.detectors.items():
            if rec.detected and now - rec.timestamp < 10:
                signals.append(f"{st}:{rec.direction}")
        return signals

    def calc(self, delta: float) -> int:
        weights = {
            "DELTA": 40, "SPOOFING": 30, "ABSORPTION": 10, "PRICE_RESPONSE": 15,
            "ICEBERG": 5, "IMBALANCE": 10, "WALL": 15, "LIQUIDITY_SHIFT": 8,
            "TAPE_SPEED": 5, "VOLUME_CLUSTER": 7, "TRADE_VELOCITY": 5,
        }

        total = 0
        bullish = 0
        bearish = 0
        now = time.time()

        for st, rec in self.detectors.items():
            if rec.detected and now - rec.timestamp < 10:
                weight = weights.get(st, 10)
                total += weight
                if rec.direction == "BULLISH":
                    bullish += weight
                elif rec.direction == "BEARISH":
                    bearish += weight

        self.bias = (bullish - bearish) / max(total, 1) * 100 if total > 0 else 0
        return total


class OrderbookProcessor:
    def __init__(self, stats=None):
        self.curr_bids: Dict[float, int] = {}
        self.curr_asks: Dict[float, int] = {}
        self.prev_bids: Dict[float, int] = {}
        self.prev_asks: Dict[float, int] = {}
        self.bid_size: int = 0
        self.ask_size: int = 0
        self.stats = stats

    def update(self, bids: List[Tuple[float, int]], asks: List[Tuple[float, int]], timestamp: float):
        self.prev_bids = self.curr_bids.copy()
        self.prev_asks = self.curr_asks.copy()
        self.curr_bids = {price: size for price, size in bids[:20]}
        self.curr_asks = {price: size for price, size in asks[:20]}
        self.bid_size = sum(self.curr_bids.values())
        self.ask_size = sum(self.curr_asks.values())
        if self.stats:
            self.stats.book_updates += 1


class SpoofDetector:
    def detect(self, prev_bids, prev_asks, curr_bids, curr_asks, journal, logger) -> bool:
        detected = False
        thr = getattr(config, 'SPOOF_SIZE_THRESHOLD', 3000)

        for price, size in prev_bids.items():
            if size >= thr and price not in curr_bids:
                journal.set("SPOOFING", {"side": "BID", "price": price, "size": size},
                            f"BID {price:.4f} removed", "BEARISH")
                detected = True
                logger.warning(f"🎭 SPOOFING BID")

        for price, size in prev_asks.items():
            if size >= thr and price not in curr_asks:
                journal.set("SPOOFING", {"side": "ASK", "price": price, "size": size},
                            f"ASK {price:.4f} removed", "BULLISH")
                detected = True
                logger.warning(f"🎭 SPOOFING ASK")

        return detected


class IcebergDetector:
    def __init__(self):
        self.history = deque(maxlen=100)

    def update(self, volume: int, timestamp: float, journal, logger) -> bool:
        self.history.append({'volume': volume, 'time': timestamp})
        if len(self.history) >= 3:
            volumes = [h['volume'] for h in list(self.history)[-5:]]
            if len(set(volumes)) == 1 and volumes[0] >= 500:
                journal.set("ICEBERG", {"volume": volumes[0]}, f"V={volumes[0]}", "")
                logger.warning(f"🧊 ICEBERG")
                return True
        return False


class TapeSpeedDetector:
    def __init__(self):
        self.trades = deque(maxlen=100)

    def update(self, journal, logger) -> bool:
        now = time.time()
        cutoff = now - 1
        while self.trades and self.trades[0] < cutoff:
            self.trades.popleft()
        self.trades.append(now)

        if len(self.trades) >= getattr(config, 'TAPE_SPEED_THRESHOLD', 15):
            speed = len(self.trades)
            journal.set("TAPE_SPEED", {"speed": speed}, f"{speed} t/s", "")
            logger.warning(f"⚡ TAPE SPEED {speed}")
            return True
        return False


class DeltaTracker:
    def __init__(self):
        self.delta = 0

    def update(self, signed_volume: int) -> int:
        self.delta += signed_volume
        return self.delta