"""Kapı açma butonları."""

from __future__ import annotations

from homeassistant.components.button import ButtonEntity
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from . import DnakeConfigEntry
from .api import DnakeError
from .const import RELAY_INDEX


async def async_setup_entry(
    hass: HomeAssistant,
    entry: DnakeConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    async_add_entities([DnakeUnlockButton(entry, RELAY_INDEX)])


class DnakeUnlockButton(ButtonEntity):
    """Röleyi tetikleyip kapıyı açar."""

    _attr_has_entity_name = True
    _attr_translation_key = "unlock"
    _attr_icon = "mdi:door-open"

    def __init__(self, entry: DnakeConfigEntry, relay_index: int) -> None:
        self._api = entry.runtime_data.api
        self._relay_index = relay_index
        self._attr_unique_id = f"{entry.entry_id}_unlock_{relay_index}"
        self._attr_device_info = entry.runtime_data.device_info

    async def async_press(self) -> None:
        try:
            await self._api.async_unlock(self._relay_index)
        except DnakeError as err:
            raise HomeAssistantError(str(err)) from err
