import asyncio
import logging

from db import DB
from obd_client import OBDClient

POLL_HZ = 5

log = logging.getLogger("collector")


async def run(client: OBDClient, db: DB) -> None:
    """
    Background polling loop.
    """
    period = 1.0 / POLL_HZ
    loop = asyncio.get_running_loop()
    next_tick = loop.time()
    last_mil: bool | None = None
    last_dtc_count: int | None = None
    last_dtcs: set[str] = set()

    while True:
        try:
            if not client.is_connected():
                log.warning("lost connection, reconnecting")
                await client.connect()

            sample = await client.read_live()
            if sample.samples:
                db.write_samples(sample)

            status_changed = (sample.mil is not None and sample.mil != last_mil) or (
                sample.dtc_count is not None and sample.dtc_count != last_dtc_count
            )
            if status_changed:
                log.info(
                    "status change: mil %s->%s count %s->%s",
                    last_mil,
                    sample.mil,
                    last_dtc_count,
                    sample.dtc_count,
                )
                dtcs = await client.read_dtcs()
                new = dtcs.current.keys() - last_dtcs
                cleared = last_dtcs - dtcs.current.keys()
                last_dtcs = set(dtcs.current)
                db.write_dtcs(dtcs, new=new, cleared=cleared)
                if new:
                    freeze = await client.read_freeze()
                    db.write_freeze(freeze)
            last_mil = sample.mil
            last_dtc_count = sample.dtc_count
        except asyncio.CancelledError:
            raise
        except Exception:
            log.exception("tick failed")
            await asyncio.sleep(1)

        next_tick += period
        sleep_for = next_tick - loop.time()
        if sleep_for > 0:
            await asyncio.sleep(sleep_for)
        else:
            next_tick = loop.time()
