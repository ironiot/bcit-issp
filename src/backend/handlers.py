from datetime import datetime

from db import DriveCycle, Dtc, LiveSample, Vehicle
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload


class QueryError(Exception):
    pass


class QueryHandler:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_all_vehicles(self) -> list[Vehicle]:
        """Return all known vehicles."""

        result = await self.session.scalars(select(Vehicle))
        return list(result.all())

    async def get_vehicle(self, vin: str) -> Vehicle | None:
        """Return a vehicle by VIN, or None if not found."""

        return await self.session.get(Vehicle, vin)

    async def get_drive_cycles(
        self,
        *,
        vin: str | None = None,
        limit: int | None,
        start_time: datetime | None,
        end_time: datetime | None,
        active_only: bool = False,
    ) -> list[DriveCycle]:
        """Return drive cycles, ordered by start time descending.
        Optional filters:
        - VIN
        - time range,
        - number of results returned
        - active drive cycles only (i.e. not ended)
        """

        stmt = select(DriveCycle).order_by(DriveCycle.start_time.desc())
        if vin:
            stmt = stmt.where(DriveCycle.vin == vin)
        if start_time:
            stmt = stmt.where(DriveCycle.start_time >= start_time)
        if end_time:
            stmt = stmt.where(DriveCycle.start_time <= end_time)
        if limit:
            stmt = stmt.limit(limit)
        if active_only:
            stmt = stmt.where(DriveCycle.end_time == None)  # noqa: E711
            # cannot use `end_time is none`, `==` has special handling by SQLAlchemy

        result = await self.session.scalars(stmt)
        return list(result.all())

    async def get_samples_in_drive_cycle(self, drive_cycle_id: int) -> list[LiveSample]:
        """Return sample metrics for a given drive cycle, ordered by timestamp ascending."""

        if not (drive_cycle := await self.session.get(DriveCycle, drive_cycle_id)):
            raise QueryError(f"Drive cycle not found: {drive_cycle_id}")

        start_time = drive_cycle.start_time
        end_time = drive_cycle.end_time

        stmt = (
            select(LiveSample)
            .where(LiveSample.timestamp >= start_time)
            .order_by(LiveSample.timestamp.asc())
        )
        if end_time:
            stmt = stmt.where(LiveSample.timestamp <= end_time)

        result = await self.session.scalars(stmt)
        return list(result.all())

    async def get_samples_in_time_range(
        self,
        vin: str,
        start_time: datetime | None = None,
        end_time: datetime | None = None,
    ) -> list[LiveSample]:
        """Return sample metrics for a given VIN and time range, ordered by timestamp ascending."""

        stmt = (
            select(LiveSample)
            .where(LiveSample.vin == vin)
            .order_by(LiveSample.timestamp.asc())
        )
        if start_time:
            stmt = stmt.where(LiveSample.timestamp >= start_time)
        if end_time:
            stmt = stmt.where(LiveSample.timestamp <= end_time)

        result = await self.session.scalars(stmt)
        return list(result.all())

    async def get_dtcs(
        self,
        *,
        limit: int | None = None,
        start_time: datetime | None = None,
        end_time: datetime | None = None,
        active_only: bool = False,
        code: str | None = None,
        vin: str | None = None,
    ) -> list[Dtc]:
        """Return DTCs ordered by timestamp descending.
        Optional filters:
        - VIN
        - time range
        - number of results returned
        - active DTCs only (i.e. not cleared)
        - code
        """

        stmt = (
            select(Dtc)
            .options(selectinload(Dtc.freeze_frame))
            .order_by(Dtc.timestamp.desc())
        )
        if vin:
            stmt = stmt.where(Dtc.vin == vin)
        if limit:
            stmt = stmt.limit(limit)
        if start_time:
            stmt = stmt.where(Dtc.timestamp >= start_time)
        if end_time:
            stmt = stmt.where(Dtc.timestamp <= end_time)
        if active_only:
            stmt = stmt.where(Dtc.cleared_at == None)  # noqa: E711
            # cannot use `cleared_at is none`, `==` has special handling by SQLAlchemy
        if code:
            stmt = stmt.where(Dtc.code == code)

        result = await self.session.scalars(stmt)
        return list(result.all())
