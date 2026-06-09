from enum import Enum
from dataclasses import dataclass
from typing import Dict, Any
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

WEIGHTS = {
    SignalType.ABSORPTION: 35,
    SignalType.PRICE_RESPONSE: 30,
    SignalType.ICEBERG: 35,
    SignalType.IMBALANCE: 25,
    SignalType.SPOOFING: 40,
    SignalType.DELTA: 30,
    SignalType.WALL: 35,
    SignalType.LIQUIDITY_SHIFT: 30,
    SignalType.TAPE_SPEED: 15,
    SignalType.VOLUME_CLUSTER: 20,
    SignalType.TRADE_VELOCITY: 10,
}
MAX_SCORE = sum(WEIGHTS.values())

TTL_CONFIG = {
    "absorption": 15, "price_response": 10, "iceberg": 30,
    "imbalance": 5, "spoofing": 10, "delta": 20,
    "wall": 10, "liquidity_shift": 5, "tape_speed": 3,
    "volume_cluster": 10, "trade_velocity": 5,
}

@dataclass
class DetectorStatus:
    name: str
    weight: int
    detected: bool = False
    value: Any = None
    details: str = ""
    timestamp: float = 0
    direction: str = ""

class DetectorJournal:
    def __init__(self):
        self.reset()
    def reset(self):
        self.detectors = {st: DetectorStatus(st.value, w) for st, w in WEIGHTS.items()}
        self.score = 0
        self.active = 0
        self.bias = 0.0
    def set(self, st, value=None, details="", direction=""):
        now = time.time()
        self.detectors[st].detected = True
        self.detectors[st].value = value
        self.detectors[st].details = details
        self.detectors[st].timestamp = now
        self.detectors[st].direction = direction
    def calc(self, stats_delta=None):
        now = time.time()
        self.score = 0
        self.active = 0
        bullish = bearish = 0
        for st, det in self.detectors.items():
            if not det.detected:
                continue
            if now - det.timestamp > TTL_CONFIG.get(st.value, 10):
                continue
            self.score += det.weight
            self.active += 1
            if det.direction == "BULLISH":
                bullish += det.weight
            elif det.direction == "BEARISH":
                bearish += det.weight
        self.bias = (bullish - bearish) / 10
        return self.score
    def get_components(self):
        now = time.time()
        return {d.name.lower(): d.weight for d in self.detectors.values()
                if d.detected and (now - d.timestamp) <= TTL_CONFIG.get(d.name.lower(), 10)}
    def get_signals(self):
        now = time.time()
        return {d.name.lower(): {"weight": d.weight, "value": d.value, "direction": d.direction}
                for d in self.detectors.values()
                if d.detected and (now - d.timestamp) <= TTL_CONFIG.get(d.name.lower(), 10)}
