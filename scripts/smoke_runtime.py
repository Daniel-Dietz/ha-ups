"""Exercise real Home Assistant and a pinned Parcel Aggregator without UPS access.

All shipments in this test are synthetic. The UPS carrier client is patched
only within the test; no account, browser credentials or network are needed.
"""

import argparse
import asyncio
from datetime import UTC, datetime, timedelta
from pathlib import Path
import shutil
import sys
from tempfile import TemporaryDirectory
from unittest.mock import AsyncMock, patch

from homeassistant import bootstrap, loader
from homeassistant.config_entries import SOURCE_USER, ConfigEntry, ConfigEntryState
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType
from homeassistant.helpers import entity_registry as er

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from tests.payloads import active_sample, delivered_sample  # noqa: E402

CODE = "EXAMPLE000000"


async def create_entry(hass: HomeAssistant, domain: str) -> ConfigEntry:
    """Create a config entry through the real Home Assistant UI flow."""
    result = await hass.config_entries.flow.async_init(
        domain, context={"source": SOURCE_USER}
    )
    if result["type"] is FlowResultType.FORM:
        result = await hass.config_entries.flow.async_configure(result["flow_id"], {})
    assert result["type"] is FlowResultType.CREATE_ENTRY
    await hass.async_block_till_done()
    entry = result["result"]
    assert entry.state is ConfigEntryState.LOADED
    return entry


def state_by_uid(hass: HomeAssistant, platform: str, domain: str, uid: str):
    """Resolve the stable unique ID regardless of the localized entity ID."""
    entity_id = er.async_get(hass).async_get_entity_id(platform, domain, uid)
    assert entity_id is not None, uid
    state = hass.states.get(entity_id)
    assert state is not None, uid
    return state


async def run_runtime(aggregator_source: Path) -> None:
    """Verify real config flows, registry discovery, deduplication and events."""
    with TemporaryDirectory(prefix="ups-ha-smoke-") as tmp:
        config_dir = Path(tmp)
        shutil.copytree(
            ROOT / "custom_components/ups", config_dir / "custom_components/ups"
        )
        shutil.copytree(
            aggregator_source / "custom_components/parcel_aggregator",
            config_dir / "custom_components/parcel_aggregator",
        )
        sys.path.insert(0, tmp)
        hass = HomeAssistant(tmp)
        loader.async_setup(hass)
        hass.config.skip_pip = True
        try:
            assert await bootstrap.async_from_config_dict(
                {
                    "homeassistant": {
                        "name": "UPS smoke test",
                        "latitude": 0,
                        "longitude": 0,
                        "elevation": 0,
                        "time_zone": "Europe/Berlin",
                        "unit_system": "metric",
                        "country": "DE",
                        "language": "de",
                    }
                },
                hass,
            )
            # Load aggregator first: it must discover the German UPS entity
            # created later, using stable unique IDs, not English entity IDs.
            aggregator = await create_entry(hass, "parcel_aggregator")
            sample = active_sample(CODE)
            sample.update(
                {
                    "sdd": (datetime.now(UTC) + timedelta(days=1)).strftime("%Y%m%d"),
                    "sdst": "13:00:00",
                    "sdt": "15:00:00",
                    "shipToAddress": {"country": "DE"},
                    "shipmentGMTInfo": {"shipToGMTOffset": "+00:00"},
                }
            )
            events = []
            hass.bus.async_listen("parcel_aggregator_parcel_registered", events.append)
            delivered_events = []
            hass.bus.async_listen(
                "parcel_aggregator_parcel_delivered", delivered_events.append
            )
            with patch(
                "custom_components.ups.api.UPSApiClient.async_get_parcel",
                new=AsyncMock(return_value=sample),
            ) as fetch:
                ups = await create_entry(hass, "ups")
                fetch.assert_not_called()
                uid = f"{ups.entry_id}_incoming_parcels"
                assert state_by_uid(hass, "sensor", "ups", uid).state == "0"
                assert (
                    state_by_uid(
                        hass,
                        "sensor",
                        "parcel_aggregator",
                        "parcel_aggregator_incoming",
                    ).state
                    == "0"
                )

                await hass.services.async_call(
                    "ups", "track_parcel", {"tracking_code": CODE}, blocking=True
                )
                await hass.async_block_till_done()
                incoming = state_by_uid(hass, "sensor", "ups", uid)
                assert incoming.state == "1"
                assert incoming.attributes["parcels"][0]["barcode"] == CODE
                fetch.assert_awaited_once()
                aggregate = state_by_uid(
                    hass, "sensor", "parcel_aggregator", "parcel_aggregator_incoming"
                )
                assert aggregate.state == "1"
                parcel = aggregate.attributes["parcels"][0]
                assert parcel["barcode"] == CODE
                assert parcel["carrier"] == "UPS"
                assert parcel["status"] == "out_for_delivery"
                assert "raw" not in parcel
                assert parcel["planned_from"]
                assert parcel["planned_to"]
                assert state_by_uid(
                    hass, "calendar", "ups", f"{ups.entry_id}_deliveries"
                ).state in {"on", "off"}
                assert state_by_uid(hass, "button", "ups", f"{ups.entry_id}_refresh")
                # An actual second source in the registry stands in for a
                # shop reporting the same synthetic parcel.
                duplicate = er.async_get(hass).async_get_or_create(
                    "sensor",
                    "amazon_orders",
                    "smoke_shop_incoming_parcels",
                    suggested_object_id="smoke_shop_incoming",
                )
                hass.states.async_set(
                    duplicate.entity_id,
                    "1",
                    {"parcels": [{**parcel, "carrier": "ups", "contents": "Example"}]},
                )
                await hass.async_block_till_done()
                aggregate = state_by_uid(
                    hass, "sensor", "parcel_aggregator", "parcel_aggregator_incoming"
                )
                assert aggregate.state == "1"
                assert aggregate.attributes["parcels"][0]["contents"] == "Example"
                assert len(events) == 1
                assert events[0].data["barcode"] == CODE
                assert "raw" not in events[0].data
                # Remove the synthetic shop source and deliver the parcel via
                # the production normalization/publish path, without changing
                # the real request budget or waiting hours for another poll.
                hass.states.async_remove(duplicate.entity_id)
                er.async_get(hass).async_remove(duplicate.entity_id)
                await hass.async_block_till_done()
                delivered = delivered_sample(CODE)
                today = datetime.now(UTC).strftime("%Y%m%d")
                delivered["shipmentProgressActivities"][0]["gmtDate"] = today
                coordinator = ups.runtime_data.coordinator
                coordinator.async_set_updated_data(coordinator._publish([delivered]))  # noqa: SLF001
                await hass.async_block_till_done()
                assert state_by_uid(hass, "sensor", "ups", uid).state == "0"
                assert (
                    state_by_uid(
                        hass,
                        "sensor",
                        "parcel_aggregator",
                        "parcel_aggregator_delivered",
                    ).state
                    == "1"
                )
                assert len(delivered_events) == 1
                assert delivered_events[0].data["barcode"] == CODE
                assert "raw" not in delivered_events[0].data
                assert await hass.config_entries.async_unload(ups.entry_id)
                assert await hass.config_entries.async_unload(aggregator.entry_id)
                await hass.async_block_till_done()
                assert ups.state is ConfigEntryState.NOT_LOADED
                assert aggregator.state is ConfigEntryState.NOT_LOADED
                assert not hass.services.has_service("ups", "track_parcel")
            print(
                "PASS: HA core + UPS + Parcel Aggregator runtime, German locale, service, deduplication, events, calendar, button, unload"
            )
        finally:
            await hass.async_stop(force=True)
            sys.path.remove(tmp)


def main() -> None:
    """Parse the required upstream checkout path and run the smoke test."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--aggregator-source", type=Path, required=True)
    args = parser.parse_args()
    asyncio.run(run_runtime(args.aggregator_source.resolve()))


if __name__ == "__main__":
    main()
