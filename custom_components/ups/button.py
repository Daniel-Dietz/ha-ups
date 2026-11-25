"""Budget-aware manual refresh for UPS."""

from __future__ import annotations

from homeassistant.components.button import ButtonEntity
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import UPSConfigEntry
from .device import ATTRIBUTION, build_device_info

PARALLEL_UPDATES = 0


async def async_setup_entry(
    hass: HomeAssistant,
    entry: UPSConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Expose the refresh button on the existing UPS device."""
    async_add_entities([UPSRefreshButton(entry)])


class UPSRefreshButton(ButtonEntity):
    """Request a normal coordinator refresh without bypassing rate limits."""

    _attr_has_entity_name = True
    _attr_translation_key = "refresh"
    _attr_attribution = ATTRIBUTION

    def __init__(self, entry: UPSConfigEntry) -> None:
        """Bind the button to the configured coordinator."""
        self._entry = entry
        self._attr_unique_id = f"{entry.entry_id}_refresh"
        self._attr_device_info = build_device_info(entry)

    async def async_press(self) -> None:
        """Request one budget-controlled refresh."""
        await self._entry.runtime_data.coordinator.async_request_refresh()
