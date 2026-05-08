import unittest
from unittest.mock import Mock, AsyncMock, patch
from sqlalchemy.ext.asyncio import AsyncSession

from db.reader import DBReader
from db.model  import (
    DriveCycle,
    Dtc
)


class TestDBReader(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.session = AsyncMock()
        self.reader = DBReader(self.session)

    async def test_get_all_vehicles(self):
        ...

    async def test_get_vehicle_exist(self):
        ...

    async def test_get_vehicle_not_exist(self):
        ...

    async def test_get_vehicle_stats(self):
        fake_drive_cycles = [DriveCycle(id=1), DriveCycle(id=2)]
        fake_dtcs = [Dtc(code="P0300"), Dtc(code="P0420")]
        fake_max_metrics = Mock()
        for metric in [
                "rpm", "speed", "engine_load",
                "throttle_pos", "maf", "map"
        ]:
            setattr(fake_max_metrics, f"max_{metric}", 000)

        self.reader.get_drive_cycles = (
            AsyncMock(return_value=fake_drive_cycles)
        )
        self.reader.get_dtcs = AsyncMock(return_value=fake_dtcs)
        self.reader._get_aggregated_metrics = (
            AsyncMock(return_value=fake_max_metrics)
        )
        stats = await self.reader.get_vehicle_stats(vin="ABC123")
        expected = {
            "drive_cycles_count": 2,
            "active_dtc_codes": ["P0300", "P0420"],
            "max_rpm": 123,
            "max_speed": 123,
            "max_engine_load": 123,
            "max_throttle_pos": 123,
            "max_maf": 123,
            "max_map": 123,
        }
        self.assertDictEqual(stats, expected)

if __name__ == "__main__":
    unittest.main()
