#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from typing import Dict, List, Tuple
import time


class OrderbookProcessor:
    def __init__(self, stats=None):
        self.curr_bids: Dict[float, int] = {}
        self.curr_asks: Dict[float, int] = {}
        self.prev_bids: Dict[float, int] = {}
        self.prev_asks: Dict[float, int] = {}
        self.bid_size: int = 0
        self.ask_size: int = 0
        self.stats = stats
        self._last_update = 0

    def update(self, bids: List[Tuple[float, int]], asks: List[Tuple[float, int]], timestamp: float):
        """Обновление стакана"""
        # Сохраняем предыдущее состояние
        self.prev_bids = self.curr_bids.copy()
        self.prev_asks = self.curr_asks.copy()

        # Обновляем текущее (топ 20 уровней)
        self.curr_bids = {price: size for price, size in bids[:20]}
        self.curr_asks = {price: size for price, size in asks[:20]}

        # Считаем общий объем
        self.bid_size = sum(self.curr_bids.values())
        self.ask_size = sum(self.curr_asks.values())

        self._last_update = timestamp

        if self.stats:
            self.stats.book_updates += 1

    def get_top_bid(self) -> Tuple[float, int]:
        """Лучший бид"""
        if self.curr_bids:
            price = max(self.curr_bids.keys())
            return price, self.curr_bids[price]
        return 0, 0

    def get_top_ask(self) -> Tuple[float, int]:
        """Лучший аск"""
        if self.curr_asks:
            price = min(self.curr_asks.keys())
            return price, self.curr_asks[price]
        return 0, 0

    def get_spread(self) -> float:
        """Спред"""
        bid_price, _ = self.get_top_bid()
        ask_price, _ = self.get_top_ask()
        if bid_price > 0 and ask_price > 0:
            return ask_price - bid_price
        return 0