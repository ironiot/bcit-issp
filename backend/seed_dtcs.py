import asyncio
from datetime import datetime, timezone

from dotenv import load_dotenv
from sqlalchemy import select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from db.model import Dtc, FreezeFrame, get_DB_URL

load_dotenv()

# (vin, code, description, freeze frame kwargs)
SEEDS = [
    (
        "WP0ZZZ99ZTS390001",
        "P0420",
        "Catalyst system efficiency below threshold",
        dict(RPM=2200, SPEED=68, ENGINE_LOAD=42.5, THROTTLE_POS=18.0, MAP=31.2, COOLANT_TEMP=91.0),
    ),
    (
        "WP0ZZZ99ZTS390001",
        "P0301",
        "Cylinder 1 misfire detected",
        dict(RPM=1800, SPEED=44, ENGINE_LOAD=36.0, THROTTLE_POS=12.0, MAP=28.7, COOLANT_TEMP=88.0),
    ),
    (
        "JM3KFBDM5K0123456",
        "P0171",
        "System too lean (Bank 1)",
        dict(RPM=2400, SPEED=72, ENGINE_LOAD=51.0, THROTTLE_POS=22.0, MAP=33.5, COOLANT_TEMP=93.0),
    ),
]


async def main():
    engine = create_async_engine(f"postgresql+asyncpg://{get_DB_URL()}")
    Session = async_sessionmaker(engine, expire_on_commit=False)

    async with Session() as session:
        for vin, code, desc, freeze_kwargs in SEEDS:
            existing = await session.execute(
                select(Dtc).where(
                    Dtc.vin == vin, Dtc.code == code, Dtc.cleared_at.is_(None)
                )
            )
            if existing.scalar_one_or_none():
                print(f"skip {vin} {code} (already active)")
                continue

            dtc = Dtc(
                vin=vin,
                code=code,
                description=desc,
                timestamp=datetime.now(timezone.utc),
                cleared_at=None,
            )
            session.add(dtc)
            await session.flush()

            session.add(FreezeFrame(dtc_id=dtc.id, **freeze_kwargs))
            print(f"seeded {vin} {code}")

        await session.commit()

    await engine.dispose()


asyncio.run(main())
