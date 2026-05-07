import logging
from typing import TypedDict

from aiohttp import ClientSession

log = logging.getLogger("vpic")


class VPICVehicleInfo(TypedDict):
    model: str | None  # e.g. "Honda Accord 2021"
    body_type: str | None  # e.g. "Sedan"
    fuel_type: str | None  # e.g. "Gasoline"
    transmission: str | None  # e.g. "Automatic"
    drive_type: str | None  # e.g. "Front-Wheel Drive"


async def fetch_vpic_data(client: ClientSession, vin: str) -> VPICVehicleInfo | None:
    """Query NHTSA VPIC API for vehicle info from VIN."""

    url = f"https://vpic.nhtsa.dot.gov/api/vehicles/DecodeVin/{vin}?format=json"

    try:
        async with client.get(url) as response:
            data = await response.json()

            if response.status != 200:
                log.error(f"VPIC API error for {vin=}: {data}")
                return None

            results = {item["Variable"]: item["Value"] for item in data["Results"]}
            log.info(f"VPIC data: {results}")

            return VPICVehicleInfo(
                model=(
                    f"{results.get('Make') or ''} "
                    f"{results.get('Model') or ''} "
                    f"{results.get('Model Year') or ''}"
                ).strip()
                or None,
                body_type=results.get("Body Class"),
                fuel_type=results.get("Fuel Type - Primary"),
                transmission=results.get("Transmission Style"),
                drive_type=results.get("Drive Type"),
            )
    except Exception as e:
        log.error(f"Error fetching VPIC data for {vin=}: {e}")
        return None
