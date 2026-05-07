import asyncio
import logging

from obd_client import OBDClient

from main import DBWriter

POLL_PERIOD = 5  # seconds
ENGINE_ON_VOLTAGE = 13.0

log = logging.getLogger("collector")


async def run(client: OBDClient, db: DBWriter) -> None:
    """
    Background polling loop.
    """

    loop = asyncio.get_running_loop()
    next_tick = loop.time()
    last_mil: bool | None = None
    last_dtc_count: int | None = None
    last_dtcs: set[str] = set()
    engine_on: bool = False

    while True:
        try:
            if not client.is_connected():
                log.warning("lost connection, reconnecting")
                await client.connect()
                engine_on = False

            voltage = await client.read_voltage()
            is_high_voltage = voltage is not None and voltage > ENGINE_ON_VOLTAGE

            if is_high_voltage and not engine_on:
                log.info(
                    "voltage %s > %s, starting drive cycle", voltage, ENGINE_ON_VOLTAGE
                )
                engine_on = True
                await db.start_drive_cycle()
            elif not is_high_voltage and engine_on:
                log.info(
                    "voltage %s <= %s, ending drive cycle", voltage, ENGINE_ON_VOLTAGE
                )
                engine_on = False
                await db.end_drive_cycle()

            if engine_on:
                sample = await client.read_live()
                if sample.samples:
                    await db.write_sample(sample)

                status_changed = (
                    sample.mil is not None and sample.mil != last_mil
                ) or (
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
                    if new or cleared:
                        await db.write_dtcs(dtcs, new=new, cleared=cleared)
                    if new:
                        freeze = await client.read_freeze()
                        await db.write_freeze(freeze)
                last_mil = sample.mil
                last_dtc_count = sample.dtc_count
            else:  # don't poll anything if engine is off, let the ECU sleep
                pass

        except asyncio.CancelledError:
            raise
        except Exception:
            log.exception("tick failed")
            await asyncio.sleep(1)

        next_tick += POLL_PERIOD
        sleep_for = next_tick - loop.time()
        if sleep_for > 0:
            await asyncio.sleep(sleep_for)
        else:
            next_tick = loop.time()
