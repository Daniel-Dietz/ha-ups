"""Import the real HA core and exercise pure production contracts."""

from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from custom_components.ups.api import _retry_after
from custom_components.ups.const import ParcelStatus
from custom_components.ups.parcels import normalize_parcel


def main() -> None:
    """Exercise data normalization and retry parsing on the installed HA."""
    parcel = normalize_parcel({"requestedTrackingNumber": "EXAMPLE000000"})
    assert parcel["barcode"] == "EXAMPLE000000"
    assert parcel["status"] is ParcelStatus.UNKNOWN
    assert _retry_after("120") == 120
    assert _retry_after("not a date") is None


if __name__ == "__main__":
    main()
