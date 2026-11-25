"""Diagnostics support for the UPS parcel tracker integration."""

from __future__ import annotations

# Only canonical state counts and controlled transport telemetry are exported.
from collections import Counter
from typing import Any

from homeassistant.core import HomeAssistant

from . import UPSConfigEntry
from .const import ParcelStatus


def _status_counts(parcels: list[dict[str, Any]]) -> dict[str, int]:
    """Count only known status values; never export a parcel identifier."""
    known = {status.value for status in ParcelStatus}
    return dict(
        Counter(
            status if isinstance(status, str) and status in known else "unknown"
            for parcel in parcels
            for status in (parcel.get("status"),)
        )
    )


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant, entry: UPSConfigEntry
) -> dict[str, Any]:
    """Return diagnostics for the UPS config entry."""
    coordinator = entry.runtime_data.coordinator

    return {
        "counts": {
            "incoming_active": len(coordinator.data or []),
            "delivered": len(coordinator.delivered or []),
        },
        "polling": {
            "tier_minutes": coordinator.current_tier_minutes,
            "update_interval_seconds": (
                coordinator.update_interval.total_seconds()
                if coordinator.update_interval
                else None
            ),
            "suspended": coordinator.update_interval is None,
            # The two numbers a throttle report is unreadable without: how
            # long the coordinator has been backing off, and whether the
            # fetch floor is currently suppressing refreshes.
            "consecutive_failed_cycles": coordinator.consecutive_failures,
            "seconds_since_last_fetch": coordinator.seconds_since_last_fetch,
        },
        # Per-request durations and outcomes, oldest first. Rising durations
        # followed by timeouts is the throttle's signature, and this is the
        # only place it can be read back after the fact — nobody has debug
        # logging on before the problem happens. Carries no tracking codes.
        "recent_fetches": [
            {"seconds": item["seconds"], "ok": item["ok"]}
            for item in coordinator.recent_fetches
        ],
        "incoming_status_counts": _status_counts(coordinator.data or []),
        "delivered_status_counts": _status_counts(coordinator.delivered or []),
    }
