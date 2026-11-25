"""Privacy regression tests for exported diagnostics."""

from datetime import timedelta
import json
from unittest.mock import MagicMock

from custom_components.ups.diagnostics import async_get_config_entry_diagnostics


async def test_diagnostics_excludes_all_untrusted_fields(hass):
    entry = MagicMock()
    entry.options = {"password": "PRIVATE_PASSWORD"}
    coordinator = entry.runtime_data.coordinator
    coordinator.current_tier_minutes = 15
    coordinator.update_interval = timedelta(minutes=15)
    coordinator.consecutive_failures = 0
    coordinator.seconds_since_last_fetch = 12.3
    coordinator.data = [
        {
            "barcode": "PRIVATE_BARCODE",
            "contents": "PRIVATE_CONTENT",
            "status": "out_for_delivery",
            "raw": {"unanticipated_key": "PRIVATE_TOKEN"},
        },
        {"status": "PRIVATE_STATUS"},
    ]
    coordinator.delivered = [
        {"status": "delivered", "raw": {"unknown": "PRIVATE_ADDRESS"}}
    ]
    coordinator.recent_fetches = [
        {"seconds": 1.4, "ok": False, "error": "PRIVATE_ERROR", "at": "PRIVATE_DATE"}
    ]

    result = await async_get_config_entry_diagnostics(hass, entry)

    assert result["counts"] == {"incoming_active": 2, "delivered": 1}
    assert result["incoming_status_counts"] == {"out_for_delivery": 1, "unknown": 1}
    assert result["delivered_status_counts"] == {"delivered": 1}
    assert result["recent_fetches"] == [{"seconds": 1.4, "ok": False}]
    assert "PRIVATE_" not in json.dumps(result)
    assert result["polling"]["update_interval_seconds"] == 900.0


async def test_diagnostics_reports_suspended_polling(hass):
    entry = MagicMock()
    coordinator = entry.runtime_data.coordinator
    coordinator.current_tier_minutes = None
    coordinator.update_interval = None
    coordinator.consecutive_failures = 0
    coordinator.seconds_since_last_fetch = None
    coordinator.data = []
    coordinator.delivered = []
    coordinator.recent_fetches = []

    result = await async_get_config_entry_diagnostics(hass, entry)

    assert result["polling"] == {
        "tier_minutes": None,
        "update_interval_seconds": None,
        "suspended": True,
        "consecutive_failed_cycles": 0,
        "seconds_since_last_fetch": None,
    }
