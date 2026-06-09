#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import config
from detectors.signals import SignalType


class SpoofDetector:
    """Детектор спуфинга (ложные заявки)"""
    
    def detect(self, prev_bids, prev_asks, curr_bids, curr_asks, journal, logger) -> bool:
        detected = False
        thr = getattr(config, 'SPOOF_SIZE_THRESHOLD', 3000)

        # Проверяем исчезнувшие крупные биды
        for price, size in prev_bids.items():
            if size >= thr and price not in curr_bids:
                journal.set(SignalType.SPOOFING, {"side": "BID", "price": price, "size": size},
                            f"BID {price:.4f} removed x{size}", "BEARISH")
                detected = True
                logger.warning(f"🎭 SPOOFING BID removed {price:.4f} x{size}")

        # Проверяем исчезнувшие крупные аски
        for price, size in prev_asks.items():
            if size >= thr and price not in curr_asks:
                journal.set(SignalType.SPOOFING, {"side": "ASK", "price": price, "size": size},
                            f"ASK {price:.4f} removed x{size}", "BULLISH")
                detected = True
                logger.warning(f"🎭 SPOOFING ASK removed {price:.4f} x{size}")

        return detected