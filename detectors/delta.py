#!/usr/bin/env python3
# -*- coding: utf-8 -*-


class DeltaTracker:
    """Трекер дельты (cumulative delta)"""
    def __init__(self):
        self.delta = 0

    def update(self, signed_volume: int) -> int:
        """Обновление дельты с учетом направления сделки"""
        self.delta += signed_volume
        return self.delta

    def reset(self):
        """Сброс дельты"""
        self.delta = 0

    def get(self) -> int:
        """Получение текущего значения дельты"""
        return self.delta