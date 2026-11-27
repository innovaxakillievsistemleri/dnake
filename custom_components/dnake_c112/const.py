"""DNAKE C112 sabitleri."""

from __future__ import annotations

DOMAIN = "dnake_c112"
MANUFACTURER = "DNAKE"
MODEL = "C112"

CONF_RTSP_PORT = "rtsp_port"
CONF_RTSP_PATH = "rtsp_path"
CONF_WEBHOOK_ID = "webhook_id"

CONF_RING_DURATION = "ring_duration"
CONF_LOCAL_ONLY = "local_only"

DEFAULT_USERNAME = "admin"
DEFAULT_RTSP_PORT = 8554
DEFAULT_RTSP_PATH = "ch01"
DEFAULT_RING_DURATION = 30
DEFAULT_LOCAL_ONLY = True

# C112 datasheet V1.8: tek röle çıkışı (DNAKE index=0 -> Röle 1)
RELAY_INDEX = 0

EVENT_RING = "ring"
BUS_EVENT_RING = f"{DOMAIN}_ring"


def signal_ring(entry_id: str) -> str:
    """Zil sinyali adı (dispatcher)."""
    return f"{DOMAIN}_{entry_id}_ring"
