#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
import time
import logging
import requests
from dataclasses import dataclass
from typing import Optional, Dict, List

import config

logger = logging.getLogger('ai')


@dataclass
class AIResult:
    direction: str
    confidence: int
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
        headers = {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json',
        }

        base_url = f'{self.api_url}/v1' if '/v1' not in self.api_url else self.api_url

        data = {
            'model': config.VSEGPT_MODEL,
            'messages': [{'role': 'user', 'content': prompt}],
            'temperature': config.VSEGPT_TEMPERATURE,
            'max_tokens': config.VSEGPT_MAX_TOKENS,
        }

        try:
            response = requests.post(
                f'{base_url}/chat/completions',
                json=data,
                headers=headers,
                timeout=timeout,
            )

            if response.status_code == 200:
                result = response.json()
                usage = result.get('usage', {})
                prompt_tokens = usage.get('prompt_tokens', 0)
                completion_tokens = usage.get('completion_tokens', 0)

                cost_input = prompt_tokens * 0.15 / 1_000_000
                cost_output = completion_tokens * 0.60 / 1_000_000
                cost_total = cost_input + cost_output

                self.total_cost += cost_total
                self.total_tokens += usage.get('total_tokens', 0)
                self.requests_count += 1

                logger.info(f"🤖 VseGPT: {self.total_tokens} tokens, ${cost_total:.6f} (total: ${self.total_cost:.6f})")
                return result
            else:
                logger.error(f"VseGPT error {response.status_code}: {response.text[:200]}")
                return None
        except Exception as e:
            logger.error(f"VseGPT error: {e}")
            return None


class AIAnalyzer:
    def __init__(self):
        self.last_call_time = 0
        self.last_context = None
        self.mode = "full"
        self.vsegpt_client = None

        if config.VSEGPT_API_KEY:
            self.vsegpt_client = VseGPTClient(config.VSEGPT_API_KEY, config.VSEGPT_API_URL)
            logger.info("✅ VseGPT client initialized")

    def set_mode(self, mode: str):
        self.mode = mode
        logger.info(f"AI mode set to {mode}")

    async def analyze(self, price: float, volume: int, score: int,
                      delta: float, vwap: float, components: Dict,
                      signals: List[str], bias: float) -> Optional[AIResult]:

        if self.mode == "fallback":
            return self._fallback_analysis(price, volume, score, delta, bias, components)

        # Cooldown check
        now = time.time()
        if now - self.last_call_time < config.AI_COOLDOWN_SECONDS:
            remaining = config.AI_COOLDOWN_SECONDS - (now - self.last_call_time)
            logger.info(f"⏱️ AI cooldown: {remaining:.0f}s remaining")
            return None

        # Bias check
        if abs(bias) < config.MIN_BIAS_FOR_AI:
            logger.info(f"Bias too low: {bias:.1f} < {config.MIN_BIAS_FOR_AI}")
            return None

        self.last_call_time = now
        return await self._call_ai_api(price, volume, score, delta, bias, signals, components)

    async def _call_ai_api(self, price: float, volume: int, score: int,
                           delta: float, bias: float, signals: List[str],
                           components: Dict) -> Optional[AIResult]:
        if not self.vsegpt_client:
            return self._fallback_analysis(price, volume, score, delta, bias, components)

        prompt = f"""Проанализируй торговый сетап для {config.TICKER}.

Параметры:
- Score: {score} (сила сигнала)
- Bias: {bias:.1f} (смещение)
- Delta: {delta:+,}
- Цена: {price:.4f}

Активные сигналы: {', '.join(signals) if signals else 'нет'}

Ответь ТОЛЬКО JSON:
{{
    "direction": "LONG/SHORT/NONE",
    "confidence": 0-100,
    "stop_ticks": 20-50,
    "take_ticks": 40-100,
    "reason": "краткое объяснение"
}}"""

        try:
            response = self.vsegpt_client.generate(prompt, timeout=30)
            if response and 'choices' in response:
                content = response['choices'][0]['message']['content']
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

        # Экстремальная защита
        if delta < -10000 and bias <= -3:
            return AIResult("NONE", 0, 0, 0, "Экстремальная дельта запрещает LONG")
        if delta > 10000 and bias >= 3:
            return AIResult("NONE", 0, 0, 0, "Экстремальная дельта запрещает SHORT")

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
            reason=f"Fallback: bias={bias:.1f}, delta={delta}"
        )


ai_analyzer = AIAnalyzer()