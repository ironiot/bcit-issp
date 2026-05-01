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


class LiveData(Base):
    __tablename__ = "live_data"

    id = Column(Integer, primary_key=True, autoincrement=True)
    timestamp = Column(DateTime(timezone=True), server_default=func.now(), index=True)

    # These are the PIDs that AI told me are important and almost universally supported.
    # Should be revised later, just a POC for now.
    rpm = Column(Float)
    speed = Column(Float)
    engine_load = Column(Float)
    throttle_pos = Column(Float)
    run_time = Column(Float)
    maf = Column(Float)
    short_fuel_trim_1 = Column(Float)
    long_fuel_trim_1 = Column(Float)
    coolant_temp = Column(Float)
    intake_temp = Column(Float)
    control_module_voltage = Column(Float)
    fuel_level = Column(Float)

    errors = relationship("Error", back_populates="live_data")


class Error(Base):
    __tablename__ = "error"

    id = Column(Integer, primary_key=True, autoincrement=True)
    live_data_id = Column(Integer, ForeignKey("live_data.id"))
    error_code = Column(String(5), nullable=False, index=True)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())

    live_data = relationship("LiveData", back_populates="errors")


def main():
    engine = create_engine("postgresql+psycopg://bcit-issp@localhost/ironiot")
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)


if __name__ == "__main__":
    main()
