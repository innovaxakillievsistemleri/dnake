"""DNAKE C112 kamerası (RTSP)."""

from __future__ import annotations

from haffmpeg.tools import IMAGE_JPEG, ImageFrame

from homeassistant.components.camera import Camera, CameraEntityFeature
from homeassistant.components.ffmpeg import get_ffmpeg_manager
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from . import DnakeConfigEntry


async def async_setup_entry(
    hass: HomeAssistant,
    entry: DnakeConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    async_add_entities([DnakeCamera(entry)])


class DnakeCamera(Camera):
    """C112 canlı görüntüsü.

    stream_source verildiği için Home Assistant'ın yerleşik go2rtc'si
    görüntüyü kendiliğinden WebRTC ile (düşük gecikme) sunar.
    """

    _attr_has_entity_name = True
    _attr_translation_key = "door"
    _attr_supported_features = CameraEntityFeature.STREAM
    _attr_brand = "DNAKE"
    _attr_model = "C112"

    def __init__(self, entry: DnakeConfigEntry) -> None:
        super().__init__()
        self._api = entry.runtime_data.api
        self._attr_unique_id = f"{entry.entry_id}_camera"
        self._attr_device_info = entry.runtime_data.device_info

    async def stream_source(self) -> str | None:
        return self._api.rtsp_url

    async def async_camera_image(
        self, width: int | None = None, height: int | None = None
    ) -> bytes | None:
        """Anlık görüntü (bildirim fotoğrafı ve kart önizlemesi için)."""
        ffmpeg = ImageFrame(get_ffmpeg_manager(self.hass).binary)
        return await ffmpeg.get_image(
            self._api.rtsp_url,
            output_format=IMAGE_JPEG,
            extra_cmd="-rtsp_transport tcp",
        )
