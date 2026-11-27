"""DNAKE C112 kapı paneli entegrasyonu."""

from __future__ import annotations

from dataclasses import dataclass
import logging

from aiohttp import web

from homeassistant.components import webhook
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST, CONF_PASSWORD, CONF_USERNAME, Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.dispatcher import async_dispatcher_send

from .api import DnakeC112
from .const import (
    BUS_EVENT_RING,
    CONF_LOCAL_ONLY,
    CONF_RTSP_PATH,
    CONF_RTSP_PORT,
    CONF_WEBHOOK_ID,
    DEFAULT_LOCAL_ONLY,
    DEFAULT_RTSP_PATH,
    DEFAULT_RTSP_PORT,
    DOMAIN,
    MANUFACTURER,
    MODEL,
    signal_ring,
)

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[Platform] = [
    Platform.BINARY_SENSOR,
    Platform.BUTTON,
    Platform.CAMERA,
    Platform.EVENT,
]


@dataclass
class DnakeData:
    """Config entry çalışma verisi."""

    api: DnakeC112
    device_info: DeviceInfo


type DnakeConfigEntry = ConfigEntry[DnakeData]


async def async_setup_entry(hass: HomeAssistant, entry: DnakeConfigEntry) -> bool:
    """Config entry kur."""
    api = DnakeC112(
        async_get_clientsession(hass),
        entry.data[CONF_HOST],
        entry.data[CONF_USERNAME],
        entry.data[CONF_PASSWORD],
        entry.data.get(CONF_RTSP_PORT, DEFAULT_RTSP_PORT),
        entry.data.get(CONF_RTSP_PATH, DEFAULT_RTSP_PATH),
    )
    device_info = DeviceInfo(
        identifiers={(DOMAIN, entry.entry_id)},
        manufacturer=MANUFACTURER,
        model=MODEL,
        name=entry.title,
        configuration_url=f"http://{api.host}",
    )
    entry.runtime_data = DnakeData(api=api, device_info=device_info)

    async def _handle_webhook(
        hass: HomeAssistant, webhook_id: str, request: web.Request
    ) -> web.Response:
        """C112'nin HTTP komutu zile basıldığında buraya gelir."""
        _LOGGER.debug(
            "Zil webhook'u geldi: %s %s", request.method, request.remote
        )
        async_dispatcher_send(hass, signal_ring(entry.entry_id))
        hass.bus.async_fire(
            BUS_EVENT_RING,
            {"entry_id": entry.entry_id, "name": entry.title},
        )
        return web.Response(text="OK")

    webhook.async_register(
        hass,
        DOMAIN,
        f"{entry.title} zil",
        entry.data[CONF_WEBHOOK_ID],
        _handle_webhook,
        local_only=entry.options.get(CONF_LOCAL_ONLY, DEFAULT_LOCAL_ONLY),
        allowed_methods=["GET", "POST", "PUT"],
    )

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    entry.async_on_unload(entry.add_update_listener(_async_options_updated))
    return True


async def _async_options_updated(hass: HomeAssistant, entry: DnakeConfigEntry) -> None:
    """Seçenekler değişince yeniden yükle."""
    await hass.config_entries.async_reload(entry.entry_id)


async def async_unload_entry(hass: HomeAssistant, entry: DnakeConfigEntry) -> bool:
    """Config entry kaldır."""
    webhook.async_unregister(hass, entry.data[CONF_WEBHOOK_ID])
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
