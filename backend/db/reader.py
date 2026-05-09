from datetime import datetime
from typing import Mapping

from db.model import DriveCycle, Dtc, LiveSample, Vehicle
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload


class QueryError(Exception):
    pass


_AGGREGATABLE_METRICS = ["rpm", "speed", "engine_load", "throttle_pos", "maf", "map"]


class DBReader:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_all_vehicles(self) -> list[Vehicle]:
        """Return all known vehicles."""

        result = await self.session.scalars(select(Vehicle))
        return list(result.all())

    async def get_vehicle(self, vin: str) -> Vehicle | None:
        """Return a vehicle by VIN, or None if not found."""

        return await self.session.get(Vehicle, vin)

    async def get_vehicle_stats(self, vin: str):
        """Return aggregated stats for a vehicle. Include
        - number of drive cycles
        - first measure timestamp
        - last measure timestamp
        - total number of DTCs
        - active DTC codes
        - measured distance
        """

        drive_cycles_count = len(await self.get_drive_cycles(vin=vin))

        all_dtcs = await self.get_dtcs(vin=vin)
        total_dtcs_count = len(all_dtcs)
        active_dtcs = list(set(dtc.code for dtc in all_dtcs if not dtc.cleared_at))

        first_measure = await self.session.scalar(
            select(LiveSample.timestamp)
            .where(LiveSample.vin == vin)
            .order_by(LiveSample.timestamp.asc())
        )
        last_measure = await self.session.scalar(
            select(LiveSample.timestamp)
            .where(LiveSample.vin == vin)
            .order_by(LiveSample.timestamp.desc())
        )

        distance = (
            await self.session.scalar(
                select(func.sum(DriveCycle.distance)).where(DriveCycle.vin == vin)
            )
            or 0
        )
        # If there are active drive cycles, calculate distance for them as well
        # This looks like an N+1 query, but in practice there should be at most 1 active drive cycle.
        for active_drive in await self.get_drive_cycles(vin, active_only=True):
            samples = await self._get_samples_in_drive_cycle(active_drive)
            distance += calculate_distance(samples)

        return {
            "drive_cycles_count": drive_cycles_count,
            "total_dtcs_count": total_dtcs_count,
            "active_dtcs": active_dtcs,
            "first_measure": first_measure,
            "last_measure": last_measure,
            "distance": distance,
        }

    async def get_drive_cycle_stats(
        self, drive_cycle_id: int
    ) -> Mapping[str, float | None]:
        """Return aggregated stats for a drive cycle."""

        if not (drive := await self.session.get(DriveCycle, drive_cycle_id)):
            raise QueryError(f"Drive cycle not found: {drive_cycle_id}")

        if not (samples := await self._get_samples_in_drive_cycle(drive)):
            raise QueryError(f"No samples found for drive cycle: {drive_cycle_id}")

        aggregated_metrics = await self._get_aggregated_metrics(
            vin=drive.vin,
            start_time=drive.start_time,
            end_time=drive.end_time,
        )

        if (distance := drive.distance) is None:
            distance = calculate_distance(samples)

        stats = {"distance": distance}
        stats.update({
            f"avg_{metric}": getattr(aggregated_metrics, f"avg_{metric}")
            for metric in _AGGREGATABLE_METRICS
        })
        stats.update({
            f"max_{metric}": getattr(aggregated_metrics, f"max_{metric}")
            for metric in _AGGREGATABLE_METRICS
        })
        stats.update({
            f"min_{metric}": getattr(aggregated_metrics, f"min_{metric}")
            for metric in _AGGREGATABLE_METRICS
        })
        return stats

    async def get_drive_cycles(
        self,
        vin: str,
        *,
        start_time: datetime | None = None,
        end_time: datetime | None = None,
        active_only: bool = False,
    ) -> list[DriveCycle]:
        """Return drive cycles for a VIN, ordered by start time descending.
        Optional filters:
        - time range,
        - active drive cycles only (i.e. not ended)
        """

        stmt = (
            select(DriveCycle)
            .where(DriveCycle.vin == vin)
            .order_by(DriveCycle.start_time.desc())
        )
        if start_time:
            stmt = stmt.where(DriveCycle.start_time >= start_time)
        if end_time:
            stmt = stmt.where(DriveCycle.start_time <= end_time)
        if active_only:
            stmt = stmt.where(DriveCycle.end_time == None)  # noqa: E711
            # cannot use `end_time is none`, `==` has special handling by SQLAlchemy

        result = await self.session.scalars(stmt)
        return list(result.all())

    async def get_samples_in_drive_cycle(self, drive_cycle_id: int) -> list[LiveSample]:
        """Return sample metrics for a given drive cycle, ordered by timestamp ascending."""

        if not (drive := await self.session.get(DriveCycle, drive_cycle_id)):
            raise QueryError(f"Drive cycle not found: {drive_cycle_id}")

        return await self._get_samples_in_drive_cycle(drive)

    async def _get_samples_in_drive_cycle(self, drive: DriveCycle) -> list[LiveSample]:
        return await self.get_samples_in_time_range(
            vin=drive.vin, start_time=drive.start_time, end_time=drive.end_time
        )

    async def get_samples_in_time_range(
        self,
        vin: str,
        *,
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
        vin: str,
        *,
        start_time: datetime | None = None,
        end_time: datetime | None = None,
        active_only: bool = False,
        code: str | None = None,
    ) -> list[Dtc]:
        """Return DTCs for a VIN, ordered by timestamp descending.
        Optional filters:
        - time range
        - active DTCs only (i.e. not cleared)
        - code
        """

        stmt = (
            select(Dtc)
            .where(Dtc.vin == vin)
            .options(selectinload(Dtc.freeze_frame))
            .order_by(Dtc.timestamp.desc())
        )
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

    async def _get_aggregated_metrics(
        self,
        vin: str,
        start_time: datetime | None = None,
        end_time: datetime | None = None,
    ):
        stmt = select(
            *[
                func.avg(getattr(LiveSample, metric)).label(f"avg_{metric}")
                for metric in _AGGREGATABLE_METRICS
            ],
            *[
                func.max(getattr(LiveSample, metric)).label(f"max_{metric}")
                for metric in _AGGREGATABLE_METRICS
            ],
            *[
                func.min(getattr(LiveSample, metric)).label(f"min_{metric}")
                for metric in _AGGREGATABLE_METRICS
            ],
        ).where(LiveSample.vin == vin)
        if start_time:
            stmt = stmt.where(LiveSample.timestamp >= start_time)
        if end_time:
            stmt = stmt.where(LiveSample.timestamp <= end_time)

        result = await self.session.execute(stmt)
        if not (row := result.first()):
            raise QueryError("No samples found in the given time range")

        return row


def calculate_distance(samples: list[LiveSample]) -> float:
    # using speed and time difference between samples

    distance = 0
    for i in range(1, len(samples)):
        prev = samples[i - 1]
        curr = samples[i]

        speed_prev = prev.speed or 0  # speed in km/h
        speed_curr = curr.speed or 0
        avg_speed = (speed_prev + speed_curr) / 2.0

        delta_hours = (curr.timestamp - prev.timestamp).total_seconds() / 3600.0
        distance += avg_speed * delta_hours

    return distance
