"""'Zil çalıyor' sensörü: zile basılınca belirli süre açık kalır."""

from __future__ import annotations

from collections.abc import Callable
from datetime import datetime

from homeassistant.components.binary_sensor import BinarySensorEntity
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback
from homeassistant.helpers.event import async_call_later

from . import DnakeConfigEntry
from .const import CONF_RING_DURATION, DEFAULT_RING_DURATION, signal_ring


async def async_setup_entry(
    hass: HomeAssistant,
    entry: DnakeConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    async_add_entities([DnakeRingingSensor(entry)])


class DnakeRingingSensor(BinarySensorEntity):
    """Zil çalıyor."""

    _attr_has_entity_name = True
    _attr_translation_key = "ringing"
    _attr_is_on = False

    def __init__(self, entry: DnakeConfigEntry) -> None:
        self._entry_id = entry.entry_id
        self._duration = entry.options.get(CONF_RING_DURATION, DEFAULT_RING_DURATION)
        self._attr_unique_id = f"{entry.entry_id}_ringing"
        self._attr_device_info = entry.runtime_data.device_info
        self._cancel_off: Callable[[], None] | None = None

    @property
    def icon(self) -> str:
        return "mdi:bell-ring" if self.is_on else "mdi:bell-outline"

    async def async_added_to_hass(self) -> None:
        self.async_on_remove(
            async_dispatcher_connect(
                self.hass, signal_ring(self._entry_id), self._handle_ring
            )
        )
        self.async_on_remove(self._cancel_timer)

    @callback
    def _cancel_timer(self) -> None:
        if self._cancel_off:
            self._cancel_off()
            self._cancel_off = None

    @callback
    def _handle_ring(self) -> None:
        self._cancel_timer()
        self._attr_is_on = True
        self.async_write_ha_state()
        self._cancel_off = async_call_later(self.hass, self._duration, self._turn_off)

    @callback
    def _turn_off(self, _now: datetime) -> None:
        self._cancel_off = None
        self._attr_is_on = False
        self.async_write_ha_state()
