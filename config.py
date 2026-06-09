import os
from pathlib import Path
from platformdirs import user_data_dir, user_log_dir, user_config_dir

APP_NAME = "tglass"
APP_AUTHOR = "tglass"

# Автоматические пути для разных ОС
DATA_DIR = Path(user_data_dir(APP_NAME, APP_AUTHOR))
LOGS_DIR = Path(user_log_dir(APP_NAME, APP_AUTHOR))
CONFIG_DIR = Path(user_config_dir(APP_NAME, APP_AUTHOR))

# Создаем директории
for d in [DATA_DIR, LOGS_DIR, CONFIG_DIR]:
    d.mkdir(parents=True, exist_ok=True)

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
TICKER = os.environ.get("TRADERNET_TICKER", "TECHSMART")

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

# ========== ПОРОГИ ДЕТЕКТОРОВ ==========
MIN_PRINT_VOLUME = int(os.environ.get("MIN_PRINT_VOLUME", "500"))
MIN_DELTA_VOLUME = int(os.environ.get("MIN_DELTA_VOLUME", "200"))
DELTA_THRESHOLD = int(os.environ.get("DELTA_THRESHOLD", "7000"))
TAPE_SPEED_THRESHOLD = int(os.environ.get("TAPE_SPEED_THRESHOLD", "15"))
ABSORPTION_THRESHOLD = int(os.environ.get("ABSORPTION_THRESHOLD", "2000"))
BIG_WALL_SIZE = int(os.environ.get("BIG_WALL_SIZE", "5000"))
SPOOF_SIZE_THRESHOLD = int(os.environ.get("SPOOF_SIZE_THRESHOLD", "3000"))
ICEBERG_MIN_VOLUME = int(os.environ.get("ICEBERG_MIN_VOLUME", "500"))
ICEBERG_TOTAL_VOLUME = int(os.environ.get("ICEBERG_TOTAL_VOLUME", "3000"))
ICEBERG_MIN_TRADES = int(os.environ.get("ICEBERG_MIN_TRADES", "8"))
PRICE_RESPONSE_THRESHOLD = int(os.environ.get("PRICE_RESPONSE_THRESHOLD", "1000"))
PRICE_TICK = float(os.environ.get("PRICE_TICK", "0.005"))

# ========== MAX BOT CONFIGURATION ==========
MAX_BOT_TOKEN = os.environ.get("MAX_BOT_TOKEN", "")
MAX_CHAT_ID = int(os.environ.get("MAX_CHAT_ID", "0"))

print("=" * 50)
print(f"📊 T-GLASS v19.1 | {TICKER}")
print(f"   DATA_DIR: {DATA_DIR}")
print(f"   LOGS_DIR: {LOGS_DIR}")
print("-" * 30)
print(f"   Setup Score Required: {SETUP_SCORE_REQUIRED}")
print(f"   AI Confidence Required: {AI_CONFIDENCE_REQUIRED}%")
print(f"   AI Cooldown: {AI_COOLDOWN_SECONDS}s")
print(f"   AI Model: {VSEGPT_MODEL if VSEGPT_API_KEY else 'FALLBACK'}")
print("-" * 30)
print(f"   MIN_PRINT_VOLUME: {MIN_PRINT_VOLUME}")
print(f"   MIN_DELTA_VOLUME: {MIN_DELTA_VOLUME}")
print(f"   DELTA_THRESHOLD: {DELTA_THRESHOLD}")
print(f"   TAPE_SPEED_THRESHOLD: {TAPE_SPEED_THRESHOLD}")
print(f"   ICEBERG_TOTAL_VOLUME: {ICEBERG_TOTAL_VOLUME}")
print(f"   ICEBERG_MIN_TRADES: {ICEBERG_MIN_TRADES}")
print("=" * 50)