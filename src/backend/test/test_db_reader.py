import unittest
from unittest.mock import AsyncMock

from db.reader import DBReader


class TestDBReader(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.mock_session = AsyncMock()
        self.reader = DBReader(self.mock_session)

    async def test_get_all_vehicles(self):
        ...

    async def test_get_vehicle_exist(self):
        ...

    async def test_get_vehicle_not_exist(self):
        ...

    async def test_get_vehicle_stats(self):
        ...

    async def test_get_drive_cycle_stats(self):
        ...

if __name__ == "__main__":
    unittest.main()

