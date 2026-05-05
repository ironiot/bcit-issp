from db import DriveCycle, LiveSample, Vehicle
from sqlalchemy import select
from sqlalchemy.orm import Session


class QueryError(Exception):
    pass


class QueryHandler:
    def __init__(self, session: Session):
        self.session = session

    def get_vehicles(self):
        """Return all known vehicles."""

        return list(self.session.scalars(select(Vehicle)))

    def get_drive_cycles(self, vin: str, limit: int):
        """Return drive cycles for a given VIN, ordered by start time descending."""

        return list(
            self.session.scalars(
                select(DriveCycle)
                .where(DriveCycle.vin == vin)
                .order_by(DriveCycle.start_time.desc())
                .limit(limit)
            )
        )

    def get_sample_metrics(self, vin: str, drive_cycle_id: int, fields: list[str]):
        """Return sample metrics for a given VIN and drive cycle, limited to the specified fields."""

        if not (drive_cycle := self.session.get(DriveCycle, drive_cycle_id)):
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

        return list(self.session.execute(stmt).mappings())
