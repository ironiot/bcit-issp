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


# These are the PIDs that AI told me are important and almost universally supported.
# Should be revised later, just a POC for now.


# Poll every 1s
class LiveDataFast(Base):
    __tablename__ = "live_data_fast"

    id = Column(Integer, primary_key=True, autoincrement=True)
    timestamp = Column(DateTime(timezone=True), server_default=func.now(), index=True)

    rpm = Column(Float)
    speed = Column(Float)
    engine_load = Column(Float)
    throttle_pos = Column(Float)
    maf = Column(Float)
    map = Column(Float)
    short_fuel_trim_1 = Column(Float)
    short_fuel_trim_2 = Column(Float)
    o2_b1s1 = Column(Float)
    o2_b2s1 = Column(Float)
    timing_advance = Column(Float)

    errors = relationship("Error", back_populates="live_data_fast")


# Poll every 10s
class LiveDataSlow(Base):
    __tablename__ = "live_data_slow"

    id = Column(Integer, primary_key=True, autoincrement=True)
    timestamp = Column(DateTime(timezone=True), server_default=func.now(), index=True)

    run_time = Column(Float)
    long_fuel_trim_1 = Column(Float)
    long_fuel_trim_2 = Column(Float)
    coolant_temp = Column(Float)
    intake_temp = Column(Float)
    ambient_air_temp = Column(Float)
    control_module_voltage = Column(Float)
    fuel_level = Column(Float)
    barometric_pressure = Column(Float)
    o2_b1s2 = Column(Float)
    o2_b2s2 = Column(Float)
    distance_w_mil = Column(Float)

    errors = relationship("Error", back_populates="live_data_slow")


# Poll every 10s; only insert if a new error is detected (not every time the same error is detected)
class Error(Base):
    __tablename__ = "error"

    id = Column(Integer, primary_key=True, autoincrement=True)
    # when inserting, need to find the closest live data entry to associate with this error
    live_data_fast_id = Column(Integer, ForeignKey("live_data_fast.id"))
    live_data_slow_id = Column(Integer, ForeignKey("live_data_slow.id"))

    error_code = Column(String(5), nullable=False, index=True)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())

    live_data_fast = relationship("LiveDataFast", back_populates="errors")
    live_data_slow = relationship("LiveDataSlow", back_populates="errors")


def main():
    engine = create_engine("postgresql+psycopg://bcit-issp@localhost/ironiot")
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)


if __name__ == "__main__":
    main()
