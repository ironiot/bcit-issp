from __future__ import annotations

import asyncio
import os
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, text
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy.sql import func


class Base(DeclarativeBase):
    pass


class Vehicle(Base):
    __tablename__ = "vehicle"

    vin: Mapped[str] = mapped_column(String(17), primary_key=True)
    calibration_id: Mapped[str | None] = mapped_column(String(20))
    cvn: Mapped[str | None] = mapped_column(String(20))
    ecu_name: Mapped[str | None] = mapped_column(String(20))

    live_samples: Mapped[list[LiveSample]] = relationship(back_populates="vehicle")
    dtcs: Mapped[list[Dtc]] = relationship(back_populates="vehicle")
    drive_cycles: Mapped[list[DriveCycle]] = relationship(back_populates="vehicle")


class DriveCycle(Base):
    __tablename__ = "drive_cycle"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    vin: Mapped[str] = mapped_column(ForeignKey("vehicle.vin"), index=True)
    start_time: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), index=True
    )
    end_time: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), index=True
    )

    vehicle: Mapped[Vehicle] = relationship(back_populates="drive_cycles")


class Metrics(Base):
    __abstract__ = True

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    # These are the PIDs that AI told me are important and almost universally supported.
    # Should be revised later, just a POC for now.

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


class LiveSample(Metrics):
    # collected every 5s or so

    __tablename__ = "live_sample"

    vin: Mapped[str] = mapped_column(
        ForeignKey("vehicle.vin"), nullable=False, index=True
    )
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), index=True
    )

    vehicle: Mapped[Vehicle] = relationship(back_populates="live_samples")


class FreezeFrame(Metrics):
    # collected when there's a new DTC

    __tablename__ = "freeze_frame"

    dtc_id: Mapped[int] = mapped_column(
        ForeignKey("dtc.id"), nullable=False, index=True
    )

    dtc: Mapped[Dtc] = relationship(back_populates="freeze_frame")


class Dtc(Base):
    # errors

    __tablename__ = "dtc"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    vin: Mapped[str] = mapped_column(
        ForeignKey("vehicle.vin"), nullable=False, index=True
    )
    code: Mapped[str] = mapped_column(String(5), index=True)
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), index=True
    )
    cleared_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    freeze_frame: Mapped[FreezeFrame | None] = relationship(back_populates="dtc")
    vehicle: Mapped[Vehicle] = relationship(back_populates="dtcs")


URL_ENV_VAR = "BCIT_ISSP_DB_URL"  # "user:password@host:port/dbname"


async def main() -> None:
    if not (url := os.getenv(URL_ENV_VAR)):
        raise ValueError(f"Missing env var {URL_ENV_VAR}")

    engine = create_async_engine(f"postgresql+asyncpg://{url}")
    async with engine.begin() as conn:
        # nuke the database
        await conn.execute(text("DROP SCHEMA public CASCADE"))
        await conn.execute(text("CREATE SCHEMA public"))
        # create new tables
        await conn.run_sync(Base.metadata.create_all)


if __name__ == "__main__":
    asyncio.run(main())
