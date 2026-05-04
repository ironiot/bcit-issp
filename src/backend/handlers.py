from db import Vehicle
from sqlalchemy import select
from sqlalchemy.orm import Session


def get_vehicles(session: Session):
    """Return all known vehicles."""

    return list(session.scalars(select(Vehicle)))
