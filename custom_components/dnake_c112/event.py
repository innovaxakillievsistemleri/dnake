"""Zil olayı."""

from __future__ import annotations

from homeassistant.components.event import EventDeviceClass, EventEntity
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from . import DnakeConfigEntry
from .const import EVENT_RING, signal_ring


async def async_setup_entry(
    hass: HomeAssistant,
    entry: DnakeConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    async_add_entities([DnakeRingEvent(entry)])


class DnakeRingEvent(EventEntity):
    """Zile her basışta tetiklenir."""

    _attr_has_entity_name = True
    _attr_translation_key = "ring"
    _attr_device_class = EventDeviceClass.DOORBELL
    _attr_event_types = [EVENT_RING]

    def __init__(self, entry: DnakeConfigEntry) -> None:
        self._entry_id = entry.entry_id
        self._attr_unique_id = f"{entry.entry_id}_ring"
        self._attr_device_info = entry.runtime_data.device_info

    async def async_added_to_hass(self) -> None:
        await super().async_added_to_hass()
        self.async_on_remove(
            async_dispatcher_connect(
                self.hass, signal_ring(self._entry_id), self._handle_ring
            )
        )

    @callback
    def _handle_ring(self) -> None:
        self._trigger_event(EVENT_RING)
        self.async_write_ha_state()
