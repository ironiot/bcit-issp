from collections.abc import Sequence

from db import DriveCycle, LiveSample, Vehicle, datetime
from sqlalchemy import RowMapping, select
from sqlalchemy.ext.asyncio import AsyncSession


class QueryError(Exception):
    pass


class QueryHandler:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_vehicles(self) -> list[Vehicle]:
        """Return all known vehicles."""

        result = await self.session.scalars(select(Vehicle))
        return list(result.all())

    async def get_drive_cycles(self, vin: str, limit: int) -> list[DriveCycle]:
        """Return drive cycles for a given VIN, ordered by start time descending."""

        result = await self.session.scalars(
            select(DriveCycle)
            .where(DriveCycle.vin == vin)
            .order_by(DriveCycle.start_time.desc())
            .limit(limit)
        )
        return list(result.all())

    async def get_sample_metrics(
        self, vin: str, drive_cycle_id: int, fields: list[str]
    ) -> Sequence[RowMapping]:
        """Return sample metrics for a given VIN and drive cycle, limited to the specified fields."""

        if not (drive_cycle := await self.session.get(DriveCycle, drive_cycle_id)):
            raise QueryError(f"Drive cycle not found: {drive_cycle_id}")

        start_time = drive_cycle.start_time
        end_time = drive_cycle.end_time

        try:
            live_sample_fields = [getattr(LiveSample, f) for f in fields]
        except AttributeError:
            raise QueryError(f"Invalid field in metrics query: {fields}")

        stmt = select(LiveSample.timestamp, *live_sample_fields).where(
            LiveSample.vin == vin,
            LiveSample.timestamp >= start_time,
        )

        if end_time is not None:
            stmt = stmt.where(LiveSample.timestamp <= end_time)

        result = await self.session.execute(stmt)
        return list(result.mappings().all())
