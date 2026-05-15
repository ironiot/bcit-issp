import asyncio
from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from db.model import Dtc, FreezeFrame, get_DB_URL

VIN = "WP0ZZZ99ZTS390000"

async def main():
    engine = create_async_engine(f"postgresql+asyncpg://{get_DB_URL()}")
    Session = async_sessionmaker(engine, expire_on_commit=False)

    async with Session() as session:
        dtc1 = Dtc(
            vin=VIN,
            code="P0420",
            description="Catalyst system efficiency below threshold",
            timestamp=datetime.now(timezone.utc),
            cleared_at=None,
        )
        session.add(dtc1)
        await session.flush()  

        freeze1 = FreezeFrame(
            dtc_id=dtc1.id,
            RPM=2200,
            SPEED=68,
            ENGINE_LOAD=42.5,
            THROTTLE_POS=18.0,
            MAP=31.2,
            COOLANT_TEMP=91.0,
        )
        session.add(freeze1)

        dtc2 = Dtc(
            vin=VIN,
            code="P0301",
            description="Cylinder 1 misfire detected",
            timestamp=datetime.now(timezone.utc),
            cleared_at=None,
        )
        session.add(dtc2)
        await session.flush()

        freeze2 = FreezeFrame(
            dtc_id=dtc2.id,
            RPM=1800,
            SPEED=44,
            ENGINE_LOAD=36.0,
            THROTTLE_POS=12.0,
            MAP=28.7,
            COOLANT_TEMP=88.0,
        )
        session.add(freeze2)

        await session.commit()

    await engine.dispose()

asyncio.run(main())