from db import DriveCycle, Vehicle
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
