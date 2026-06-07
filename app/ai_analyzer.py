#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
import time
import logging
import requests
from dataclasses import dataclass
from typing import Optional, Dict, Any, List

import config

logger = logging.getLogger('ai')


@dataclass
class AIResult:
    direction: str  # LONG, SHORT, NONE
    confidence: int  # 0-100
    stop_ticks: int
    take_ticks: int
    reason: str


class VseGPTClient:
    def __init__(self, api_key, api_url):
        self.api_key = api_key
        self.api_url = api_url.rstrip('/')
        self.total_cost = 0
        self.total_tokens = 0
        self.requests_count = 0

    def generate(self, prompt, timeout=60):
        """Генерация через VseGPT"""
        headers = {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json',
        }

        if '/v1' not in self.api_url:
            base_url = f'{self.api_url}/v1'
        else:
            base_url = self.api_url

        data = {
            'model': config.VSEGPT_MODEL,
            'messages': [
                {'role': 'user', 'content': prompt},
            ],
            'temperature': config.VSEGPT_TEMPERATURE,
            'max_tokens': config.VSEGPT_MAX_TOKENS,
        }

        try:
            start_time = time.time()
            response = requests.post(
                f'{base_url}/chat/completions',
                json=data,
                headers=headers,
                timeout=timeout,
            )
            elapsed = time.time() - start_time

            if response.status_code == 200:
                result = response.json()
                usage = result.get('usage', {})
                prompt_tokens = usage.get('prompt_tokens', 0)
                completion_tokens = usage.get('completion_tokens', 0)
                total_tokens = usage.get('total_tokens', 0)

                # Примерная стоимость
                cost_input = prompt_tokens * 0.15 / 1_000_000
                cost_output = completion_tokens * 0.60 / 1_000_000
                cost_total = cost_input + cost_output

                self.total_cost += cost_total
                self.total_tokens += total_tokens
                self.requests_count += 1

                logger.info(
                    f"🤖 VseGPT: {total_tokens} токенов, ${cost_total:.6f} (всего: ${self.total_cost:.6f})")

                return result
            else:
                error_text = response.text[:200] if response.text else "No response"
                logger.error(f"❌ VseGPT ошибка {response.status_code}: {error_text}")
                return None

        except Exception as e:
            logger.error(f"❌ VseGPT ошибка: {e}")
            return None


class AIAnalyzer:
    def __init__(self):
        self.last_call_time = 0
        self.last_context = None
        self.mode = "full"
        self.vsegpt_client = None

        if config.VSEGPT_API_KEY:
            self.vsegpt_client = VseGPTClient(config.VSEGPT_API_KEY, config.VSEGPT_API_URL)
            logger.info("✅ VseGPT клиент инициализирован")

    def set_mode(self, mode: str):
        self.mode = mode
        logger.info(f"AI mode set to {mode}")

    def _check_cooldown(self) -> bool:
        """Проверка кулдауна"""
        now = time.time()
        if now - self.last_call_time < config.AI_COOLDOWN_SECONDS:
            remaining = config.AI_COOLDOWN_SECONDS - (now - self.last_call_time)
            logger.info(f"⏱️ AI cooldown: {remaining:.0f}s remaining")
            return False
        return True

    def _check_context_changed(self, delta: float, bias: float) -> bool:
        """Проверка изменения контекста"""
        context = (delta, bias)
        if self.last_context is None:
            self.last_context = context
            return True

        delta_changed = abs(delta - self.last_context[0]) >= config.MIN_DELTA_CHANGE_FOR_NEW_AI
        bias_changed = abs(bias - self.last_context[1]) >= config.MIN_BIAS_CHANGE_FOR_NEW_AI

        if delta_changed or bias_changed:
            self.last_context = context
            return True
        return False

    async def analyze(self, price: float, volume: int, score: int,
                      delta: float, vwap: float, components: Dict,
                      signals: List[str], bias: float) -> Optional[AIResult]:
        """Анализ сетапа"""

        # Fallback режим
        if self.mode == "fallback":
            return self._fallback_analysis(price, volume, score, delta, bias, components)

        # Проверка кулдауна
        if not self._check_cooldown():
            return None

        # Проверка bias
        if abs(bias) < config.MIN_BIAS_FOR_AI:
            logger.info(f"Bias too low: {bias:.1f} < {config.MIN_BIAS_FOR_AI}")
            return None

        # Проверка изменения контекста
        if not self._check_context_changed(delta, bias):
            logger.info("Context not changed, skipping AI")
            return None

        # Вызов AI
        self.last_call_time = time.time()
        return await self._call_ai_api(price, volume, score, delta, bias, signals, components)

    async def _call_ai_api(self, price: float, volume: int, score: int,
                           delta: float, bias: float, signals: List[str],
                           components: Dict) -> Optional[AIResult]:
        """Вызов AI API"""
        if not self.vsegpt_client:
            return self._fallback_analysis(price, volume, score, delta, bias, components)

        prompt = f"""Ты профессиональный трейдер. Проанализируй сетап для {config.TICKER}.

Параметры:
- Score: {score} (сила сигнала)
- Bias: {bias:.1f} (смещение, положительное = бычий)
- Delta: {delta:+,} (поток объема)
- Цена: {price:.4f}

Активные сигналы: {', '.join(signals) if signals else 'нет'}

Ответь ТОЛЬКО JSON:
{{
    "direction": "LONG" или "SHORT" или "NONE",
    "confidence": число от 0 до 100,
    "stop_ticks": число (20-50),
    "take_ticks": число (40-100),
    "reason": "краткое объяснение"
}}"""

        try:
            response = self.vsegpt_client.generate(prompt, timeout=30)
            if response and 'choices' in response:
                content = response['choices'][0]['message']['content']
                # Очищаем от markdown
                content = content.replace('```json', '').replace('```', '').strip()
                data = json.loads(content)

                return AIResult(
                    direction=data.get('direction', 'NONE'),
                    confidence=int(data.get('confidence', 0)),
                    stop_ticks=int(data.get('stop_ticks', 20)),
                    take_ticks=int(data.get('take_ticks', 40)),
                    reason=data.get('reason', 'AI анализ')
                )
        except Exception as e:
            logger.error(f"AI API error: {e}")

        return self._fallback_analysis(price, volume, score, delta, bias, components)

    def _fallback_analysis(self, price: float, volume: int, score: int,
                           delta: float, bias: float, components: Dict) -> AIResult:
        """Fallback анализ без AI"""

        # Защита от экстремальных движений
        if delta < -10000 and bias <= -3:
            return AIResult("NONE", 0, 0, 0, "Экстремальная дельта запрещает LONG")
        if delta > 10000 and bias >= 3:
            return AIResult("NONE", 0, 0, 0, "Экстремальная дельта запрещает SHORT")

        # Определяем направление
        if bias > 0 and delta > 0:
            direction = "LONG"
            confidence = min(60 + abs(bias) * 5, 85)
        elif bias < 0 and delta < 0:
            direction = "SHORT"
            confidence = min(60 + abs(bias) * 5, 85)
        else:
            direction = "NONE"
            confidence = 0

        if confidence < 60:
            direction = "NONE"

        return AIResult(
            direction=direction,
            confidence=int(confidence),
            stop_ticks=20,
            take_ticks=40,
            reason=f"Fallback анализ: bias={bias:.1f}, delta={delta}"
        )


ai_analyzer = AIAnalyzer()