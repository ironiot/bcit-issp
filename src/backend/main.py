import asyncio
import logging
from contextlib import asynccontextmanager

import collector
from aiohttp import ClientSession
from db.model import get_DB_URL
from db.writer import DBWriter
from fastapi import FastAPI
from obd_client import OBD_URL, OBDClient
from routes import router
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine


@asynccontextmanager
async def lifespan(app: FastAPI):
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )

    engine = create_async_engine(f"postgresql+asyncpg://{get_DB_URL()}")
    session_factory = async_sessionmaker(engine, expire_on_commit=False)
    http_client = ClientSession()

    app.state.obd = OBDClient(port=OBD_URL)
    db_writer = DBWriter(http_client, session_factory)

    await app.state.obd.connect()

    if not (vehicle := await app.state.obd.read_vehicle()):
        logging.error("Failed to read vehicle info, exiting")
        return

    await db_writer.write_vehicle(vehicle)

    task = asyncio.create_task(
        collector.run(app.state.obd, db_writer),
        name="collector",
    )

    try:
        yield
    finally:
        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            pass

        await app.state.obd.close()
        await http_client.close()
        await engine.dispose()


app = FastAPI(lifespan=lifespan)
app.include_router(router)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
