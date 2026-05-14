from __future__ import annotations

import asyncio
import logging
import os
import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, text, ARRAY
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy.sql import func

log = logging.getLogger("db")


class Base(DeclarativeBase):
    pass


class Vehicle(Base):
    __tablename__ = "vehicle"

    # OBD data
    vin: Mapped[str] = mapped_column(String(17), primary_key=True)
    calibration_id: Mapped[str | None] = mapped_column(String(20))
    cvn: Mapped[str | None] = mapped_column(String(20))
    supported_metrics: Mapped[list[str]] = mapped_column(
        ARRAY(String), server_default="{}"
    )

    # VPIC data: query NHTSA VPIC API for these fields before inserting a new vehicle
    model: Mapped[str | None] = mapped_column(String(50))
    body_type: Mapped[str | None] = mapped_column(String(50))
    fuel_type: Mapped[str | None] = mapped_column(String(50))
    transmission: Mapped[str | None] = mapped_column(String(50))
    drive_type: Mapped[str | None] = mapped_column(String(50))


class DriveCycle(Base):
    __tablename__ = "drive_cycle"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    vin: Mapped[str] = mapped_column(ForeignKey("vehicle.vin"), index=True)
    start_time: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), index=True
    )
    end_time: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), index=True
    )
    distance: Mapped[float | None] = mapped_column()


class Metrics(Base):
    __abstract__ = True

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    # These are the PIDs that AI told me are important and almost universally supported.
    # Should be revised later, just a POC for now.

    # Anyone wants to bet this "POC" will make it into the final product? :P

    rpm: Mapped[float | None]
    speed: Mapped[float | None]
    engine_load: Mapped[float | None]
    throttle_pos: Mapped[float | None]
    maf: Mapped[float | None]
    map: Mapped[float | None]
    short_fuel_trim_1: Mapped[float | None]
    short_fuel_trim_2: Mapped[float | None]
    long_fuel_trim_1: Mapped[float | None]
    long_fuel_trim_2: Mapped[float | None]
    o2_b1s1: Mapped[float | None]
    o2_b2s1: Mapped[float | None]
    o2_b1s2: Mapped[float | None]
    o2_b2s2: Mapped[float | None]
    timing_advance: Mapped[float | None]
    run_time: Mapped[float | None]
    coolant_temp: Mapped[float | None]
    intake_temp: Mapped[float | None]
    ambient_air_temp: Mapped[float | None]
    control_module_voltage: Mapped[float | None]
    fuel_level: Mapped[float | None]
    barometric_pressure: Mapped[float | None]
    distance_w_mil: Mapped[float | None]


COLLECTED_METRICS = [
    "rpm",
    "speed",
    "engine_load",
    "throttle_pos",
    "maf",
    "map",
    "short_fuel_trim_1",
    "short_fuel_trim_2",
    "long_fuel_trim_1",
    "long_fuel_trim_2",
    "o2_b1s1",
    "o2_b2s1",
    "o2_b1s2",
    "o2_b2s2",
    "timing_advance",
    "run_time",
    "coolant_temp",
    "intake_temp",
    "ambient_air_temp",
    "control_module_voltage",
    "fuel_level",
    "barometric_pressure",
    "distance_w_mil",
]


def _parse_metrics(data: dict[str, float]):
    return {metric: data.get(metric.upper(), None) for metric in COLLECTED_METRICS}


class LiveSample(Metrics):
    # collected every 5s or so

    __tablename__ = "live_sample"

    def __init__(self, *, vin: str, timestamp: datetime, **data: float):
        super().__init__(vin=vin, timestamp=timestamp, **_parse_metrics(data))

    vin: Mapped[str] = mapped_column(ForeignKey("vehicle.vin"), index=True)
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), index=True
    )


class FreezeFrame(Metrics):
    # collected when there's a new DTC

    __tablename__ = "freeze_frame"

    def __init__(self, *, dtc_id: uuid.UUID, **data: float):
        super().__init__(dtc_id=dtc_id, **_parse_metrics(data))

    dtc_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("dtc.id"), index=True)


class Dtc(Base):
    # errors

    __tablename__ = "dtc"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    vin: Mapped[str] = mapped_column(ForeignKey("vehicle.vin"), index=True)
    code: Mapped[str] = mapped_column(String(5), index=True)
    description: Mapped[str | None] = mapped_column(String(100))
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), index=True
    )
    cleared_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    freeze_frame: Mapped[FreezeFrame | None] = relationship()


URL_ENV_VAR = "BCIT_ISSP_DB_URL"  # "user:pass@host:port/db"


def get_DB_URL():
    if not (url := os.getenv(URL_ENV_VAR)):
        raise ValueError(f"Missing env var {URL_ENV_VAR}")
    return url


async def main() -> None:
    from dotenv import load_dotenv

    load_dotenv()
    engine = create_async_engine(f"postgresql+asyncpg://{get_DB_URL()}")
    async with engine.begin() as conn:
        # nuke the database
        await conn.execute(text("DROP SCHEMA public CASCADE"))
        await conn.execute(text("CREATE SCHEMA public"))
        # create new tables
        await conn.run_sync(Base.metadata.create_all)


if __name__ == "__main__":
    asyncio.run(main())
