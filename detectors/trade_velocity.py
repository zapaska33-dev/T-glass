import time
import config
from detectors.signals import SignalType

async def detect_trade_velocity(j, recent_trades, logger):
    now = time.time()
    recent = [t for t in recent_trades if now - t.get("time", 0) <= 3]
    vel = len(recent) / 3
    if vel >= 15:
        j.set(SignalType.TRADE_VELOCITY, {"velocity": vel}, f"{vel:.1f} t/s", "")
        logger.warning(f"🏃 VEL {vel:.1f}")
