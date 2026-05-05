from db import DriveCycle, LiveSample, Vehicle
from sqlalchemy import select
from sqlalchemy.orm import Session


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

    def get_sample_metrics(self, vin: str, drive_cycle_id: str, fields: list[str]):
        """Return sample metrics for a given VIN and drive cycle, limited to the specified fields."""

        if not (drive_cycle := self.session.get(DriveCycle, drive_cycle_id)):
            return None

        start_time = drive_cycle.start_time
        end_time = drive_cycle.end_time

        return list(
            self.session.scalars(
                select(LiveSample)
                .where(
                    LiveSample.vin == vin,
                    LiveSample.timestamp >= start_time,
                    LiveSample.timestamp <= end_time,
                )
                .with_only_columns(
                    LiveSample.timestamp, *[getattr(LiveSample, f) for f in fields]
                )
            )
        )
