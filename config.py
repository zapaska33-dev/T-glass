import os

# ========== TRADERNET ==========
PUBLIC_KEY = os.environ.get("TRADERNET_PUBLIC_KEY")
PRIVATE_KEY = os.environ.get("TRADERNET_PRIVATE_KEY")
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")

# ========== VSEGPT AI ==========
VSEGPT_API_KEY = os.environ.get("VSEGPT_API_KEY")
VSEGPT_API_URL = os.environ.get("VSEGPT_API_URL", "https://api.vsegpt.ru/v1")
VSEGPT_MODEL = os.environ.get("VSEGPT_MODEL", "anthropic/claude-3-haiku")
VSEGPT_MAX_TOKENS = int(os.environ.get("VSEGPT_MAX_TOKENS", "300"))
VSEGPT_TEMPERATURE = float(os.environ.get("VSEGPT_TEMPERATURE", "0.2"))

# ========== TICKER ==========
TICKER = os.environ.get("TRADERNET_TICKER", "VTBR")

# ========== THRESHOLDS ==========
SETUP_SCORE_REQUIRED = int(os.environ.get("SETUP_SCORE_REQUIRED", "40"))
AI_CONFIDENCE_REQUIRED = int(os.environ.get("AI_CONFIDENCE_REQUIRED", "80"))

# ========== AI COOLDOWN ==========
AI_COOLDOWN_SECONDS = int(os.environ.get("AI_COOLDOWN_SECONDS", "120"))

# ========== AI THRESHOLDS ==========
MIN_BIAS_FOR_AI = int(os.environ.get("MIN_BIAS_FOR_AI", "3"))
MIN_DELTA_FOR_AI = int(os.environ.get("MIN_DELTA_FOR_AI", "5000"))
MIN_DELTA_CHANGE_FOR_NEW_AI = int(os.environ.get("MIN_DELTA_CHANGE_FOR_NEW_AI", "3000"))
MIN_BIAS_CHANGE_FOR_NEW_AI = float(os.environ.get("MIN_BIAS_CHANGE_FOR_NEW_AI", "1.0"))

# ========== НОВЫЕ ПОВЫШЕННЫЕ ПОРОГИ ДЛЯ VTBR ==========
# Крупная сделка (было 300, стало 500)
MIN_PRINT_VOLUME = int(os.environ.get("MIN_PRINT_VOLUME", "500"))

# Минимальный объем для дельты (было 100, стало 200)
MIN_DELTA_VOLUME = int(os.environ.get("MIN_DELTA_VOLUME", "200"))

# Порог дельты для детектора (было 5000, стало 7000)
DELTA_THRESHOLD = int(os.environ.get("DELTA_THRESHOLD", "7000"))

# Скорость ленты (было 10, стало 15)
TAPE_SPEED_THRESHOLD = int(os.environ.get("TAPE_SPEED_THRESHOLD", "15"))

# Остальные пороги
ABSORPTION_THRESHOLD = int(os.environ.get("ABSORPTION_THRESHOLD", "2000"))
BIG_WALL_SIZE = int(os.environ.get("BIG_WALL_SIZE", "5000"))
SPOOF_SIZE_THRESHOLD = int(os.environ.get("SPOOF_SIZE_THRESHOLD", "3000"))
ICEBERG_MIN_VOLUME = int(os.environ.get("ICEBERG_MIN_VOLUME", "500"))
PRICE_RESPONSE_THRESHOLD = int(os.environ.get("PRICE_RESPONSE_THRESHOLD", "1000"))

print("=" * 50)
print(f"📊 VTBR DETECTOR v19.0 | {TICKER}")
print(f"   Setup Score Required: {SETUP_SCORE_REQUIRED}")
print(f"   AI Confidence Required: {AI_CONFIDENCE_REQUIRED}%")
print(f"   AI Cooldown: {AI_COOLDOWN_SECONDS}s")
print(f"   AI Model: {VSEGPT_MODEL if VSEGPT_API_KEY else 'FALLBACK'}")
print("-" * 30)
print(f"   MIN_PRINT_VOLUME: {MIN_PRINT_VOLUME} акций")
print(f"   MIN_DELTA_VOLUME: {MIN_DELTA_VOLUME} акций")
print(f"   DELTA_THRESHOLD: {DELTA_THRESHOLD} акций")
print(f"   TAPE_SPEED_THRESHOLD: {TAPE_SPEED_THRESHOLD} сделок/сек")
print("=" * 50)

# ========== MAX BOT CONFIGURATION (из секретов) ==========
MAX_BOT_TOKEN = os.environ.get("MAX_BOT_TOKEN", "")
MAX_CHAT_ID = int(os.environ.get("MAX_CHAT_ID", "0"))
