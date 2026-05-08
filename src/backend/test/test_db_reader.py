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

    async def test_get_drive_cycle_stats(self):
        ...

if __name__ == "__main__":
    unittest.main()
