import time
import config
from detectors.signals import SignalType

async def detect_volume_cluster(j, recent_trades, logger):
    now = time.time()
    recent = [t for t in recent_trades if now - t.get("time", 0) <= 10]
    minv = getattr(config, 'MIN_PRINT_VOLUME', 500)
    large = [t for t in recent if t.get("volume", 0) >= minv / 2]
    if len(large) >= 3:
        j.set(SignalType.VOLUME_CLUSTER, {"cluster_size": len(large)}, f"{len(large)} prints", "")
        logger.warning(f"📦 CLUST")
