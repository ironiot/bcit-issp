import os

from sqlalchemy import (
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    create_engine,
)
from sqlalchemy.orm import declarative_base, relationship
from sqlalchemy.sql import func

Base = declarative_base()


class VehicleMetrics(Base):
    __abstract__ = True

    id = Column(Integer, primary_key=True, autoincrement=True)
    timestamp = Column(DateTime(timezone=True), server_default=func.now(), index=True)

    # These are the PIDs that AI told me are important and almost universally supported.
    # Should be revised later, just a POC for now.

    rpm = Column(Float)
    speed = Column(Float)
    engine_load = Column(Float)
    throttle_pos = Column(Float)
    maf = Column(Float)
    map = Column(Float)
    short_fuel_trim_1 = Column(Float)
    short_fuel_trim_2 = Column(Float)
    long_fuel_trim_1 = Column(Float)
    long_fuel_trim_2 = Column(Float)
    o2_b1s1 = Column(Float)
    o2_b2s1 = Column(Float)
    o2_b1s2 = Column(Float)
    o2_b2s2 = Column(Float)
    timing_advance = Column(Float)
    run_time = Column(Float)
    coolant_temp = Column(Float)
    intake_temp = Column(Float)
    ambient_air_temp = Column(Float)
    control_module_voltage = Column(Float)
    fuel_level = Column(Float)
    barometric_pressure = Column(Float)
    distance_w_mil = Column(Float)


class LiveSample(VehicleMetrics):
    # collected every 5s or so

    __tablename__ = "live_sample"


class FreezeFrame(VehicleMetrics):
    # collected when there's a new DTC

    __tablename__ = "freeze_frame"

    dtcs = relationship("DTC", back_populates="freeze_frame")


class DTC(Base):
    # error info, there might be multiple of these for each freeze frame

    __tablename__ = "dtc"

    id = Column(Integer, primary_key=True, autoincrement=True)
    code = Column(String(5), nullable=False, index=True)
    cleared_at = Column(DateTime(timezone=True))
    freeze_frame_id = Column(
        Integer,
        ForeignKey("freeze_frame.id"),
        nullable=False,
        index=True,
    )

    freeze_frame = relationship("FreezeFrame", uselist=False, back_populates="dtcs")


URL_ENV_VAR = "BCIT_ISSP_DB_URL"  # "user:password@host:port/dbname"


def main() -> None:
    if not (url := os.getenv(URL_ENV_VAR)):
        raise ValueError(f"Missing env var {URL_ENV_VAR}")

    engine = create_engine(f"postgresql+psycopg://{url}")
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)


if __name__ == "__main__":
    main()
