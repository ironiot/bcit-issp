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


class Vehicle(Base):
    __tablename__ = "vehicle"

    vin = Column(String(17), primary_key=True)
    calibration_id = Column(String(20))
    cvn = Column(String(20))
    ecu_name = Column(String(20))

    metrics = relationship("Metrics", back_populates="vehicle")
    dtcs = relationship("DTC", back_populates="vehicle")
    drive_cycles = relationship("DriveCycle", back_populates="vehicle")


class DriveCycle(Base):
    __tablename__ = "drive_cycle"

    id = Column(Integer, primary_key=True, autoincrement=True)
    vin = Column(String(17), ForeignKey("vehicle.vin"), nullable=False, index=True)
    start_time = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    end_time = Column(DateTime(timezone=True), index=True)

    vehicle = relationship("Vehicle", uselist=False, back_populates="drive_cycles")


class Metrics(Base):
    __abstract__ = True

    id = Column(Integer, primary_key=True, autoincrement=True)
    vin = Column(String(17), ForeignKey("vehicle.vin"), nullable=False, index=True)
    timestamp = Column(DateTime(timezone=True), server_default=func.now(), index=True)

    vehicle = relationship("Vehicle", uselist=False, back_populates="metrics")

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


class LiveSample(Metrics):
    # collected every 5s or so

    __tablename__ = "live_sample"


class FreezeFrame(Metrics):
    # collected when there's a new DTC

    __tablename__ = "freeze_frame"

    dtcs = relationship("DTC", back_populates="freeze_frame")


class DTC(Base):
    # error info, there might be multiple of these for each freeze frame

    __tablename__ = "dtc"

    id = Column(Integer, primary_key=True, autoincrement=True)
    vin = Column(String(17), ForeignKey("vehicle.vin"), nullable=False, index=True)
    code = Column(String(5), nullable=False, index=True)
    cleared_at = Column(DateTime(timezone=True))
    freeze_frame_id = Column(
        Integer,
        ForeignKey("freeze_frame.id"),
        nullable=False,
        index=True,
    )

    freeze_frame = relationship("FreezeFrame", uselist=False, back_populates="dtcs")
    vehicle = relationship("Vehicle", uselist=False, back_populates="dtcs")


URL_ENV_VAR = "BCIT_ISSP_DB_URL"  # "user:password@host:port/dbname"


def main() -> None:
    if not (url := os.getenv(URL_ENV_VAR)):
        raise ValueError(f"Missing env var {URL_ENV_VAR}")

    engine = create_engine(f"postgresql+psycopg://{url}")
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)


if __name__ == "__main__":
    main()
