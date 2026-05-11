import uuid
from datetime import datetime

from db.model import DriveCycle, Dtc, LiveSample, Vehicle
from sqlalchemy import case, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload


class QueryError(Exception):
    pass


_AGGREGATABLE_METRICS = ["rpm", "speed", "engine_load", "throttle_pos", "maf", "map"]


class DBReader:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_vehicles(self) -> list[dict]:
        """Return all vehicles, including info (vehicle table) and these stats:
        - first and last measure timestamp
        - total number of DTCs
        - active DTC codes
        - number of drive cycles
        - distance travelled
        """

        if not (vehicles := await self._get_vehicles()):
            return []

        # For each vehicle, we get:

        # 1. first and last measure
        timestamps_res = await self.session.execute(
            select(
                LiveSample.vin,
                func.min(LiveSample.timestamp).label("first_measure"),
                func.max(LiveSample.timestamp).label("last_measure"),
            ).group_by(LiveSample.vin)
        )
        timestamps_map = {row.vin: row for row in timestamps_res}

        # 2. total DTC count, active DTC codes
        dtcs_res = await self.session.execute(
            select(
                Dtc.vin,
                func.count(Dtc.id).label("total_dtcs_count"),
                func.string_agg(
                    func.distinct(case((Dtc.cleared_at.is_(None), Dtc.code))), ","
                ).label("active_dtcs"),
            ).group_by(Dtc.vin)
        )
        dtcs_map = {row.vin: row for row in dtcs_res}

        # 3. Drive cycles count and total distance
        drives_res = await self.session.execute(
            select(
                DriveCycle.vin,
                func.count(DriveCycle.id).label("drive_cycles_count"),
                func.sum(DriveCycle.distance).label("distance"),
            ).group_by(DriveCycle.vin)
        )
        drives_map = {row.vin: row for row in drives_res}

        # 4. Calculate distance for active drive cycles
        # It looks like an N+1 query, but
        # there should be at most 1 active drive cycle per vehicle, so it should be fine.
        active_distances = {}
        for active_drive in await self.get_drive_cycles(active_only=True):
            samples = await self._get_samples_in_drive_cycle(active_drive)
            active_distances[active_drive.vin] = calculate_distance(samples)

        # Combine them into a list[{vin, ...info_and_stats}]

        res = []
        for v in vehicles:
            timestamps = timestamps_map.get(v.vin)
            dtcs = dtcs_map.get(v.vin)
            drives = drives_map.get(v.vin)

            vehicle_dict = {
                c.name: getattr(v, c.name, None) for c in v.__table__.columns
            }
            vehicle_dict.update({
                "drive_cycles_count": getattr(drives, "drive_cycles_count", 0),
                "total_dtcs_count": getattr(dtcs, "total_dtcs_count", 0),
                "active_dtcs": (
                    getattr(dtcs, "active_dtcs", "").split(",")
                    if getattr(dtcs, "active_dtcs", None)
                    else []
                ),
                "first_measure": getattr(timestamps, "first_measure", None),
                "last_measure": getattr(timestamps, "last_measure", None),
                "distance": getattr(drives, "distance", 0)
                + active_distances.get(v.vin, 0),
            })
            res.append(vehicle_dict)

        return res

    async def _get_vehicles(self) -> list[Vehicle]:
        result = await self.session.scalars(select(Vehicle))
        return list(result.all())

    async def get_vehicle(self, vin: str) -> Vehicle | None:
        """Return a vehicle by VIN, or None if not found."""

        return await self.session.get(Vehicle, vin)

    async def get_drive_cycle_stats(self, drive_cycle_id: uuid.UUID) -> dict:
        """Return stats for a drive cycle.
        -  distance travelled
        -  dtcs during the drive cycle
        -  average, min and max for each of the aggregatable metrics
        """

        if not (drive := await self.session.get(DriveCycle, drive_cycle_id)):
            raise QueryError(f"Drive cycle not found: {drive_cycle_id}")

        if not (samples := await self._get_samples_in_drive_cycle(drive)):
            raise QueryError(f"No samples found for drive cycle: {drive_cycle_id}")

        if (distance := drive.distance) is None:
            distance = calculate_distance(samples)

        dtcs = await self.get_dtcs(drive.vin)

        aggregated_metrics = await self._get_aggregated_metrics(
            vin=drive.vin,
            start_time=drive.start_time,
            end_time=drive.end_time,
        )
        avgs = {
            metric: getattr(aggregated_metrics, f"avg_{metric}")
            for metric in _AGGREGATABLE_METRICS
        }
        mins = {
            metric: getattr(aggregated_metrics, f"min_{metric}")
            for metric in _AGGREGATABLE_METRICS
        }
        maxes = {
            metric: getattr(aggregated_metrics, f"max_{metric}")
            for metric in _AGGREGATABLE_METRICS
        }
        metrics = {
            metric: {"min": mins[metric], "avg": avgs[metric], "max": maxes[metric]}
            for metric in _AGGREGATABLE_METRICS
        }

        stats: dict = {"distance": distance, "dtcs": dtcs}
        stats.update(metrics)
        return stats

    async def get_drive_cycles(
        self,
        vin: str | None = None,
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

        stmt = select(DriveCycle).order_by(DriveCycle.start_time.desc())
        if vin:
            stmt = stmt.where(DriveCycle.vin == vin)
        if start_time:
            stmt = stmt.where(DriveCycle.start_time >= start_time)
        if end_time:
            stmt = stmt.where(DriveCycle.start_time <= end_time)
        if active_only:
            stmt = stmt.where(DriveCycle.end_time == None)  # noqa: E711
            # cannot use `end_time is none`, `==` has special handling by SQLAlchemy

        result = await self.session.scalars(stmt)
        return list(result.all())

    async def get_samples_in_drive_cycle(
        self, drive_cycle_id: uuid.UUID
    ) -> list[LiveSample]:
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
