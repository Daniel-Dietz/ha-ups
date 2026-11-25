"""Check the button cannot bypass normal coordinator scheduling."""

from unittest.mock import AsyncMock, MagicMock

from custom_components.ups.button import UPSRefreshButton


async def test_refresh_uses_normal_coordinator():
    entry = MagicMock()
    entry.entry_id = "example"
    coordinator = entry.runtime_data.coordinator
    coordinator.async_request_refresh = AsyncMock()
    button = UPSRefreshButton(entry)

    await button.async_press()

    coordinator.async_request_refresh.assert_awaited_once_with()
    assert button.unique_id == "example_refresh"
