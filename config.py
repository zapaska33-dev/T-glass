import os

# ========== TRADERNET ==========
PUBLIC_KEY = os.environ.get("TRADERNET_PUBLIC_KEY")
PRIVATE_KEY = os.environ.get("TRADERNET_PRIVATE_KEY")

# ========== MAX BOT (вместо Telegram) ==========
MAX_BOT_TOKEN = os.environ.get("MAX_BOT_TOKEN")
MAX_CHAT_ID = os.environ.get("MAX_CHAT_ID")  # ID пользователя/чата для отправки сигналов
MAX_API_URL = os.environ.get("MAX_API_URL", "https://api.max.ru/v1")

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

# ========== ПОРОГИ ДЛЯ TECHSMART ==========
MIN_PRINT_VOLUME = int(os.environ.get("MIN_PRINT_VOLUME", "500"))
MIN_DELTA_VOLUME = int(os.environ.get("MIN_DELTA_VOLUME", "200"))
DELTA_THRESHOLD = int(os.environ.get("DELTA_THRESHOLD", "7000"))
TAPE_SPEED_THRESHOLD = int(os.environ.get("TAPE_SPEED_THRESHOLD", "15"))
ABSORPTION_THRESHOLD = int(os.environ.get("ABSORPTION_THRESHOLD", "2000"))
BIG_WALL_SIZE = int(os.environ.get("BIG_WALL_SIZE", "5000"))
SPOOF_SIZE_THRESHOLD = int(os.environ.get("SPOOF_SIZE_THRESHOLD", "3000"))
ICEBERG_MIN_VOLUME = int(os.environ.get("ICEBERG_MIN_VOLUME", "500"))
PRICE_RESPONSE_THRESHOLD = int(os.environ.get("PRICE_RESPONSE_THRESHOLD", "1000"))

# ========== MAX COMMANDS (альтернатива Telegram) ==========
# Команды будут обрабатываться через сообщения в MAX
ALLOWED_COMMANDS = ['/pause', '/resume', '/status', '/settings', '/ai_mode', '/help', '/stats']

print("=" * 50)
print(f"📊 TECHSMART DETECTOR v19.1 | {TICKER}")
print(f"   Setup Score Required: {SETUP_SCORE_REQUIRED}")
print(f"   AI Confidence Required: {AI_CONFIDENCE_REQUIRED}%")
print(f"   AI Cooldown: {AI_COOLDOWN_SECONDS}s")
print(f"   AI Model: {VSEGPT_MODEL if VSEGPT_API_KEY else 'FALLBACK'}")
print(f"   MAX Bot: {'✅' if MAX_BOT_TOKEN else '❌'}")
print("-" * 30)
print(f"   MIN_PRINT_VOLUME: {MIN_PRINT_VOLUME} акций")
print(f"   MIN_DELTA_VOLUME: {MIN_DELTA_VOLUME} акций")
print(f"   DELTA_THRESHOLD: {DELTA_THRESHOLD} акций")
print(f"   TAPE_SPEED_THRESHOLD: {TAPE_SPEED_THRESHOLD} сделок/сек")
print("=" * 50)