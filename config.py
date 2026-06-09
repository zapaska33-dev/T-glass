import os
from pathlib import Path

# ========== ПУТИ ДЛЯ ЛОГОВ ==========
LOG_DIR = Path('/data/logs')
LOG_DIR.mkdir(parents=True, exist_ok=True)

DATA_DIR = Path('/data')
CONFIG_DIR = Path('/data/config')

# ========== TRADERNET ==========
PUBLIC_KEY = os.environ.get("TRADERNET_PUBLIC_KEY")
PRIVATE_KEY = os.environ.get("TRADERNET_PRIVATE_KEY")
TICKER = os.environ.get("TRADERNET_TICKER", "TECHSMART")

# ========== MAX BOT ==========
MAX_BOT_TOKEN = os.environ.get("MAX_BOT_TOKEN")
MAX_CHAT_ID = int(os.environ.get("MAX_CHAT_ID", "0")) if os.environ.get("MAX_CHAT_ID") else 0

# ========== VSEGPT AI ==========
VSEGPT_API_KEY = os.environ.get("VSEGPT_API_KEY")
VSEGPT_API_URL = os.environ.get("VSEGPT_API_URL", "https://api.vsegpt.ru/v1")
VSEGPT_MODEL = os.environ.get("VSEGPT_MODEL", "anthropic/claude-3-haiku")
VSEGPT_MAX_TOKENS = int(os.environ.get("VSEGPT_MAX_TOKENS", "300"))
VSEGPT_TEMPERATURE = float(os.environ.get("VSEGPT_TEMPERATURE", "0.2"))

# ========== THRESHOLDS ==========
SETUP_SCORE_REQUIRED = int(os.environ.get("SETUP_SCORE_REQUIRED", "70"))
AI_CONFIDENCE_REQUIRED = int(os.environ.get("AI_CONFIDENCE_REQUIRED", "75"))
AI_COOLDOWN_SECONDS = int(os.environ.get("AI_COOLDOWN_SECONDS", "30"))

# ========== AI THRESHOLDS ==========
MIN_BIAS_FOR_AI = int(os.environ.get("MIN_BIAS_FOR_AI", "2"))
MIN_DELTA_FOR_AI = int(os.environ.get("MIN_DELTA_FOR_AI", "2500"))
MIN_DELTA_CHANGE_FOR_NEW_AI = int(os.environ.get("MIN_DELTA_CHANGE_FOR_NEW_AI", "3000"))
MIN_BIAS_CHANGE_FOR_NEW_AI = float(os.environ.get("MIN_BIAS_CHANGE_FOR_NEW_AI", "1.0"))

# ========== ПОРОГИ ДЕТЕКТОРОВ ==========
MIN_PRINT_VOLUME = int(os.environ.get("MIN_PRINT_VOLUME", "250"))
MIN_DELTA_VOLUME = int(os.environ.get("MIN_DELTA_VOLUME", "100"))
DELTA_THRESHOLD = int(os.environ.get("DELTA_THRESHOLD", "2500"))
TAPE_SPEED_THRESHOLD = int(os.environ.get("TAPE_SPEED_THRESHOLD", "15"))
ABSORPTION_THRESHOLD = int(os.environ.get("ABSORPTION_THRESHOLD", "800"))
BIG_WALL_SIZE = int(os.environ.get("BIG_WALL_SIZE", "1500"))
SPOOF_SIZE_THRESHOLD = int(os.environ.get("SPOOF_SIZE_THRESHOLD", "1000"))
ICEBERG_MIN_VOLUME = int(os.environ.get("ICEBERG_MIN_VOLUME", "500"))
ICEBERG_TOTAL_VOLUME = int(os.environ.get("ICEBERG_TOTAL_VOLUME", "3000"))
ICEBERG_MIN_TRADES = int(os.environ.get("ICEBERG_MIN_TRADES", "8"))
PRICE_RESPONSE_THRESHOLD = int(os.environ.get("PRICE_RESPONSE_THRESHOLD", "400"))
PRICE_TICK = float(os.environ.get("PRICE_TICK", "0.005"))

# ========== TELEGRAM (опционально) ==========
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")

print("=" * 50)
print(f"📊 T-GLASS v19.1 | {TICKER}")
print(f"   LOGS_DIR: {LOG_DIR}")
print("-" * 30)
print(f"   SETUP_SCORE_REQUIRED: {SETUP_SCORE_REQUIRED}")
print(f"   AI_CONFIDENCE_REQUIRED: {AI_CONFIDENCE_REQUIRED}%")
print(f"   AI_COOLDOWN_SECONDS: {AI_COOLDOWN_SECONDS}s")
print(f"   MIN_BIAS_FOR_AI: {MIN_BIAS_FOR_AI}")
print(f"   MIN_DELTA_FOR_AI: {MIN_DELTA_FOR_AI}")
print("-" * 30)
print(f"   MIN_PRINT_VOLUME: {MIN_PRINT_VOLUME}")
print(f"   MIN_DELTA_VOLUME: {MIN_DELTA_VOLUME}")
print(f"   DELTA_THRESHOLD: {DELTA_THRESHOLD}")
print(f"   TAPE_SPEED_THRESHOLD: {TAPE_SPEED_THRESHOLD}")
print(f"   ABSORPTION_THRESHOLD: {ABSORPTION_THRESHOLD}")
print(f"   BIG_WALL_SIZE: {BIG_WALL_SIZE}")
print(f"   SPOOF_SIZE_THRESHOLD: {SPOOF_SIZE_THRESHOLD}")
print(f"   ICEBERG_MIN_VOLUME: {ICEBERG_MIN_VOLUME}")
print(f"   ICEBERG_TOTAL_VOLUME: {ICEBERG_TOTAL_VOLUME}")
print(f"   ICEBERG_MIN_TRADES: {ICEBERG_MIN_TRADES}")
print(f"   PRICE_RESPONSE_THRESHOLD: {PRICE_RESPONSE_THRESHOLD}")
print("-" * 30)
print(f"   MAX_BOT_TOKEN: {'✅' if MAX_BOT_TOKEN else '❌'}")
print(f"   VSEGPT_API_KEY: {'✅' if VSEGPT_API_KEY else '❌'}")
print(f"   TRADERNET_KEYS: {'✅' if PUBLIC_KEY and PRIVATE_KEY else '❌'}")
print("=" * 50)