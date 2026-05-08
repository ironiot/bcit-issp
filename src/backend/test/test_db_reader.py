import unittest
from unittest.mock import Mock, AsyncMock, patch
from sqlalchemy.ext.asyncio import AsyncSession

from db.reader import DBReader
from db.model  import (
    DriveCycle,
    Dtc,
    Vehicle
)


class TestDBReader(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.session = AsyncMock()
        self.reader = DBReader(self.session)

    async def test_get_all_vehicles(self):
        mock_result = Mock()
        mock_result.all.return_value = []
        self.session.scalars.return_value = mock_result
        self.assertEqual(
            await self.reader.get_all_vehicles(),
            []
        )

    async def test_get_vehicle_exist(self):
        mock_get     = AsyncMock(spec = Vehicle)
        mock_get.vin = "SAMPLE_VIN"
        mock_get.calibration_id = "CAL_ID"
        mock_get.cvn = "CVN"

        mock_get.model        = None
        mock_get.body_type    = None
        mock_get.fuel_type    = None
        mock_get.transmission = None
        mock_get.drive_type   = None

        self.session.get.return_value = mock_get

        result = await self.reader.get_vehicle("SAMPLE_VIN")
        self.assertEqual(
            result.vin,
            "SAMPLE_VIN"
        )
        self.assertEqual(
            result.calibration_id,
            "CAL_ID"
        )
        self.assertEqual(
            result.cvn,
            "CVN"
        )

    async def test_get_vehicle_not_exist(self):
        self.session.get.return_value = None
        self.assertIsNone(await self
                          .reader
                          .get_vehicle("SAMPLE_VIN")
        )

    async def test_get_vehicle_stats(self):
        self.session = AsyncMock()
        fake_drive_cycles = [DriveCycle(id=1), DriveCycle(id=2)]
        fake_dtcs = [Dtc(code="P0300"), Dtc(code="P0420")]
        fake_max_metrics = Mock()
        for metric in [
                "rpm", "speed", "engine_load",
                "throttle_pos", "maf", "map"
        ]:
            setattr(fake_max_metrics, f"max_{metric}", 999)

        self.reader.get_drive_cycles = AsyncMock(
            return_value = fake_drive_cycles
        )
        self.reader.get_dtcs = AsyncMock(return_value = fake_dtcs)
        self.reader._get_aggregated_metrics = AsyncMock(
            return_value=fake_max_metrics
        )
        expected = {
            "drive_cycles_count": 2,
            "active_dtc_codes": ["P0300", "P0420"],
            "max_rpm": 999,
            "max_speed": 999,
            "max_engine_load": 999,
            "max_throttle_pos": 999,
            "max_maf": 999,
            "max_map": 999,
        }
        self.assertDictEqual(
            await self.reader.get_vehicle_stats("SAMPLE_VIN"),
            expected
        )

    async def test_get_drive_cycle_stats(self):
        ...


if __name__ == "__main__":
    unittest.main()
