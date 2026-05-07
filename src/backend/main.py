import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI

import collector
from db import DB
from obd_client import OBD_URL, OBDClient
from routes import router


@asynccontextmanager
async def lifespan(app: FastAPI):
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )

    app.state.obd = OBDClient(port=OBD_URL)
    app.state.db = DB()

    await app.state.obd.connect()

    app.state.vehicle_info = await app.state.obd.read_vehicle()
    app.state.db.write_vehicle(app.state.vehicle_info)

    task = asyncio.create_task(
        collector.run(app.state.obd, app.state.db),
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


app = FastAPI(lifespan=lifespan)
app.include_router(router)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
