import logging
import uuid

from aiohttp import ClientSession
from db.model import DriveCycle, Dtc, FreezeFrame, LiveSample, Vehicle, func
from db.reader import DBReader, calculate_distance
from obd_client import DTCPoll, FreezePoll, OBDVehicleInfo, SamplePoll
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from vpic import fetch_vpic_data

log = logging.getLogger("db_writer")

SAMPLES_BATCH_SIZE = 12  # one sample per 5s -> insert every minute
"""How many samples to collect before inserting all at once"""


class DBWriter:
    def __init__(
        self,
        http_client: ClientSession,
        session_factory: async_sessionmaker[AsyncSession],
    ):
        self.session_factory = session_factory
        self.http_client = http_client

        self.vin: str | None = None
        self.active_drive_cycle_id: uuid.UUID | None = None
        self.samples_buffer: list[LiveSample] = []
        self.new_dtcs: list[Dtc] = []

    async def write_vehicle(self, info: OBDVehicleInfo):
        self.vin = info.vin

        async with self.session_factory() as session:
            if vehicle := await session.get(Vehicle, info.vin):
                return

            vpic_data = await fetch_vpic_data(self.http_client, info.vin)
            vehicle = Vehicle(
                vin=info.vin,
                calibration_id=info.calibration_id,
                cvn=info.cvn,
                **(vpic_data or {}),
            )
            session.add(vehicle)
            await session.commit()

    async def start_drive_cycle(self):
        if not self.vin:
            log.error("Cannot start drive cycle: VIN not set")
            return

        async with self.session_factory() as session:
            # in case app crashed without ending the previous drive cycle
            await self._end_active_drive_cycles(session)

            new_drive = DriveCycle(vin=self.vin)
            session.add(new_drive)

            await session.flush()  # to get the new drive cycle ID
            self.active_drive_cycle_id = new_drive.id

            await session.commit()

    async def end_drive_cycle(self):
        if not self.vin:
            log.error("Cannot end drive cycle: VIN not set")
            return

        async with self.session_factory() as session:
            session.add_all(instances=self.samples_buffer)
            self.samples_buffer.clear()

            if self.active_drive_cycle_id and (
                drive := await session.get(DriveCycle, self.active_drive_cycle_id)
            ):
                drive.end_time = func.now()
                await self._update_drive_cycle_distance(session, drive)
            else:
                await self._end_active_drive_cycles(session)

            self.active_drive_cycle_id = None
            await session.commit()

    async def _end_active_drive_cycles(self, session: AsyncSession):
        # There should never be multiple active drive cycles for the same vehicle, but just in case, end them all.
        # TODO: find a better way to enforce this

        if not self.vin:
            log.error("Cannot end active drive cycles: VIN not set")
            return

        reader = DBReader(session)

        for drive in await reader.get_drive_cycles(self.vin, active_only=True):
            drive.end_time = func.now()
            await self._update_drive_cycle_distance(session, drive)

    async def _update_drive_cycle_distance(
        self, session: AsyncSession, drive: DriveCycle
    ):
        reader = DBReader(session)

        # to save drive cycle's end time before calculating distance
        await session.flush()
        await session.refresh(drive)

        samples = await reader._get_samples_in_drive_cycle(drive)
        drive.distance = calculate_distance(samples)

    # TODO: samples_buffer is only flushed when it hits SAMPLES_BATCH_SIZE or drive cycle ends.
    # On app shutdown, partial buffer (< 12 samples) is
    # either lost or rolled into the next cycle's first batch under a
    # misleading timestamp window. Add a flush call from the lifespan teardown in main.py.
    async def write_sample(self, poll: SamplePoll):
        if not self.vin:
            log.error("Cannot write sample: VIN not set")
            return

        # in case app starts while engine is already on
        if not self.active_drive_cycle_id:
            await self.start_drive_cycle()

        sample = LiveSample(vin=self.vin, timestamp=poll.ts, **poll.samples)
        self.samples_buffer.append(sample)

        if len(self.samples_buffer) >= SAMPLES_BATCH_SIZE:
            async with self.session_factory() as session:
                session.add_all(instances=self.samples_buffer)
                self.samples_buffer.clear()
                await session.commit()

    # TODO: clearing DTCs while engine off never gets recorded in the DB.
    # The /dtcs/clear route relies on the collector seeing a MIL/count
    # change on the next tick, but the collector's DTC handling is gated
    # on engine_on. Either poll STATUS even when engine is off, or have
    # the route mark active DTCs cleared directly here.
    async def write_dtcs(
        self, dtcs: DTCPoll, new: set[str], cleared: set[str]
    ) -> set[str]:
        if not self.vin:
            log.error("Cannot write DTCs: VIN not set")
            return set()

        async with self.session_factory() as session:
            existing = set[str]()
            reader = DBReader(session)
            for dtc in await reader.get_dtcs(vin=self.vin, active_only=True):
                if dtc.code in cleared:
                    dtc.cleared_at = dtcs.ts
                else:
                    existing.add(dtc.code)

            self.new_dtcs = [
                Dtc(
                    vin=self.vin,
                    timestamp=dtcs.ts,
                    code=code,
                    description=dtcs.current.get(code),
                )
                for code in new
                if code not in existing
            ]
            session.add_all(instances=self.new_dtcs)

            await session.commit()
            return {d.code for d in self.new_dtcs}

    async def write_freeze(self, freeze: FreezePoll):
        if not (
            dtc_id := next(
                (d.id for d in self.new_dtcs if d.code == freeze.triggering_code), None
            )
        ):
            log.error(
                "Cannot write freeze frame: no matching DTC for code %s",
                freeze.triggering_code,
            )
            return

        async with self.session_factory() as session:
            frame = FreezeFrame(dtc_id=dtc_id, **freeze.samples)
            session.add(frame)
            await session.commit()
