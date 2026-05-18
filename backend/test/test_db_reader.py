import unittest
from unittest.mock import AsyncMock, MagicMock, patch
import uuid
from datetime import datetime, timedelta

from db.model import DriveCycle, Dtc, LiveSample, Vehicle
from db.reader import DBReader, QueryError, calculate_distance


class TestDBReader(unittest.IsolatedAsyncioTestCase):
    """Unit tests for DBReader using mocked AsyncSession."""

    def setUp(self):
        self.session = AsyncMock()
        self.reader = DBReader(self.session)
        self.vin = "TESTVIN123"
        self.drive_cycle_id = uuid.uuid4()

    # -------------------------------------------------------------------------
    # _get_vehicles
    # -------------------------------------------------------------------------
    async def test_get_vehicles_empty(self):
        """Should return empty list when no vehicles exist."""
        self.session.scalars.return_value = AsyncMock()
        self.session.scalars.return_value.all = MagicMock(return_value=[])

        result = await self.reader.get_vehicles()
        self.assertEqual(result, [])

    # -------------------------------------------------------------------------
    # get_vehicle
    # -------------------------------------------------------------------------
    async def test_get_vehicle_found(self):
        vehicle = Vehicle(vin=self.vin)
        self.session.get.return_value = vehicle

        result = await self.reader.get_vehicle(self.vin)
        self.assertEqual(result, vehicle)
        self.session.get.assert_called_once_with(Vehicle, self.vin)

    async def test_get_vehicle_not_found(self):
        self.session.get.return_value = None
        result = await self.reader.get_vehicle(self.vin)
        self.assertIsNone(result)

    # -------------------------------------------------------------------------
    # get_drive_cycle_stats
    # -------------------------------------------------------------------------
    async def test_get_drive_cycle_stats_not_found(self):
        self.session.get.return_value = None
        with self.assertRaises(QueryError) as ctx:
            await self.reader.get_drive_cycle_stats(self.drive_cycle_id)
        self.assertIn("Drive cycle not found", str(ctx.exception))

    async def test_get_drive_cycle_stats_no_samples(self):
        drive = DriveCycle(vin=self.vin, start_time=datetime.now(), end_time=datetime.now())
        self.session.get.return_value = drive

        with patch.object(self.reader, "_get_samples_in_drive_cycle", return_value=[]):
            with self.assertRaises(QueryError) as ctx:
                await self.reader.get_drive_cycle_stats(self.drive_cycle_id)
            self.assertIn("No samples found", str(ctx.exception))

    async def test_get_drive_cycle_stats_success_with_distance_from_drive(self):
        start = datetime(2023, 1, 1, 0, 0, 0)
        end = datetime(2023, 1, 1, 1, 0, 0)
        drive = DriveCycle(vin=self.vin, start_time=start, end_time=end, distance=120.5)
        self.session.get.return_value = drive

        samples = [
            LiveSample(vin=self.vin, timestamp=start, rpm=1000, speed=50, engine_load=20),
            LiveSample(vin=self.vin, timestamp=end, rpm=2000, speed=70, engine_load=40),
        ]
        with patch.object(self.reader, "_get_samples_in_drive_cycle", return_value=samples):
            # Mock aggregated metrics result
            aggregated = MagicMock()
            for metric in ["rpm", "speed", "engine_load", "throttle_pos", "maf", "map"]:
                setattr(aggregated, f"avg_{metric}", 1500 if metric == "rpm" else 0)
                setattr(aggregated, f"min_{metric}", 1000 if metric == "rpm" else 0)
                setattr(aggregated, f"max_{metric}", 2000 if metric == "rpm" else 0)
            with patch.object(self.reader, "_get_aggregated_metrics", return_value=aggregated):
                with patch.object(self.reader, "get_dtcs", return_value=[]):
                    stats = await self.reader.get_drive_cycle_stats(self.drive_cycle_id)

        self.assertEqual(stats["distance"], 120.5)
        self.assertEqual(stats["dtcs"], [])
        self.assertIn("rpm", stats)
        self.assertEqual(stats["rpm"]["avg"], 1500)
        self.assertEqual(stats["rpm"]["min"], 1000)
        self.assertEqual(stats["rpm"]["max"], 2000)

    # -------------------------------------------------------------------------
    # get_drive_cycles
    # -------------------------------------------------------------------------
    async def test_get_drive_cycles_no_filters(self):
        drive = DriveCycle(vin=self.vin, start_time=datetime.now())
        scalars_mock = AsyncMock()
        scalars_mock.all = MagicMock(return_value=[drive])
        self.session.scalars.return_value = scalars_mock

        result = await self.reader.get_drive_cycles()
        self.assertEqual(result, [drive])
        self.session.scalars.assert_called_once()
        stmt = str(self.session.scalars.call_args[0][0])
        # Check that ordering is present (table name is "drive_cycle")
        self.assertIn("ORDER BY drive_cycle.start_time DESC", stmt)

    async def test_get_drive_cycles_with_filters(self):
        start = datetime(2023, 1, 1)
        end = datetime(2023, 1, 2)
        self.session.scalars.return_value.all = MagicMock(return_value=[])
        await self.reader.get_drive_cycles(vin=self.vin, start_time=start, end_time=end, active_only=True)
        self.session.scalars.assert_called_once()
        stmt = str(self.session.scalars.call_args[0][0])
        # Check WHERE clauses (table name is drive_cycle)
        self.assertIn("WHERE drive_cycle.vin = :vin_1", stmt)
        self.assertIn("drive_cycle.start_time >= :start_time_1", stmt)
        self.assertIn("drive_cycle.start_time <= :start_time_2", stmt)
        self.assertIn("drive_cycle.end_time IS NULL", stmt)

    # -------------------------------------------------------------------------
    # get_samples_in_drive_cycle
    # -------------------------------------------------------------------------
    async def test_get_samples_in_drive_cycle_not_found(self):
        self.session.get.return_value = None
        with self.assertRaises(QueryError):
            await self.reader.get_samples_in_drive_cycle(self.drive_cycle_id)

    async def test_get_samples_in_drive_cycle_found(self):
        drive = DriveCycle(vin=self.vin, start_time=datetime.now(), end_time=datetime.now())
        self.session.get.return_value = drive
        samples = [LiveSample(vin=self.vin, timestamp=datetime.now())]
        with patch.object(self.reader, "get_samples_in_time_range", return_value=samples):
            result = await self.reader.get_samples_in_drive_cycle(self.drive_cycle_id)
        self.assertEqual(result, samples)

    # -------------------------------------------------------------------------
    # get_dtcs
    # -------------------------------------------------------------------------
    async def test_get_dtcs_no_filters(self):
        dtc = Dtc(vin=self.vin, code="P0300")
        scalars_mock = AsyncMock()
        scalars_mock.all = MagicMock(return_value=[dtc])
        self.session.scalars.return_value = scalars_mock

        result = await self.reader.get_dtcs(self.vin)
        self.assertEqual(result, [dtc])
        stmt = str(self.session.scalars.call_args[0][0])
        self.assertIn("WHERE dtc.vin = :vin_1", stmt)
        self.assertIn("ORDER BY dtc.timestamp DESC", stmt)

    # -------------------------------------------------------------------------
    # _get_aggregated_metrics
    # -------------------------------------------------------------------------
    async def test_get_aggregated_metrics_success(self):
        row = MagicMock()
        for metric in ["rpm", "speed", "engine_load", "throttle_pos", "maf", "map"]:
            setattr(row, f"avg_{metric}", 10)
            setattr(row, f"min_{metric}", 5)
            setattr(row, f"max_{metric}", 15)

        # Mock the async execute method and its first() method
        mock_result = AsyncMock()
        mock_result.first = MagicMock(return_value=row)
        self.session.execute = AsyncMock(return_value=mock_result)

        res = await self.reader._get_aggregated_metrics(self.vin)
        self.assertEqual(res, row)

    async def test_get_aggregated_metrics_no_samples(self):
        # Mock result.first() to return None
        mock_result = AsyncMock()
        mock_result.first = MagicMock(return_value=None)
        self.session.execute = AsyncMock(return_value=mock_result)

        with self.assertRaises(QueryError):
            await self.reader._get_aggregated_metrics(self.vin)

    # -------------------------------------------------------------------------
    # calculate_distance (standalone function)
    # -------------------------------------------------------------------------
    def test_calculate_distance_empty(self):
        self.assertEqual(calculate_distance([]), 0)

    def test_calculate_distance_single_sample(self):
        sample = LiveSample(vin=self.vin, timestamp=datetime.now(), speed=60)


if __name__ == "__main__":
    unittest.main()
