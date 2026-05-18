import logging
from dataclasses import dataclass, field
from datetime import datetime
from uuid import UUID

from aiohttp import ClientSession
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from db.model import (
    COLLECTED_METRICS,
    DriveCycle,
    Dtc,
    FreezeFrame,
    LiveSample,
    Vehicle,
    func,
)
from db.reader import DBReader, calculate_distance
from obd_client import DTCPoll, FreezePoll, OBDVehicleInfo, SamplePoll
from vpic import fetch_vpic_data

log = logging.getLogger("db_writer")

SAMPLES_BATCH_SIZE = 12  # one sample per 5s -> insert every minute
"""How many samples to collect before inserting all at once"""


@dataclass
class ActiveDriveCycle:
    id: UUID | None
    start_time: datetime = field(default_factory=datetime.now)


class DBWriter:
    def __init__(
        self,
        http_client: ClientSession,
        session_factory: async_sessionmaker[AsyncSession],
    ):
        self.session_factory = session_factory
        self.http_client = http_client

        self.vin: str | None = None
        self.active_drive_cycle: ActiveDriveCycle | None = None
        self.samples_buffer: list[LiveSample] = []
        self.new_dtcs: list[Dtc] = []

    async def write_vehicle(self, info: OBDVehicleInfo):
        self.vin = info.vin

        supported_metrics = [
            m for m in info.supported_metrics if m in COLLECTED_METRICS
        ]

        async with self.session_factory() as session:
            if vehicle := await session.get(Vehicle, info.vin):
                vehicle.calibration_id = info.calibration_id
                vehicle.cvn = info.cvn
                vehicle.supported_metrics = supported_metrics
                await session.commit()
                return

            vpic_data = await fetch_vpic_data(self.http_client, info.vin)
            vehicle = Vehicle(
                vin=info.vin,
                calibration_id=info.calibration_id,
                cvn=info.cvn,
                supported_metrics=supported_metrics,
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

        self.active_drive_cycle = ActiveDriveCycle(id=None)
        # id None means it's not committed to the DB yet
        # We only add drive cycle after collecting 12 samples (buffer flush)
        # so that no DC ever has 0 samples

    async def end_drive_cycle(self):
        if not self.vin:
            log.error("Cannot end drive cycle: VIN not set")
            return

        async with self.session_factory() as session:
            session.add_all(instances=self.samples_buffer)
            self.samples_buffer.clear()

            if self.active_drive_cycle:
                end_time = func.now()
                if not self.active_drive_cycle.id:
                    drive = DriveCycle(
                        vin=self.vin,
                        start_time=self.active_drive_cycle.start_time,
                        end_time=end_time,
                    )
                    session.add(drive)
                elif drive := await session.get(DriveCycle, self.active_drive_cycle.id):
                    drive.end_time = end_time

                if drive:
                    await self._update_drive_cycle_distance(session, drive)
                    await session.commit()
                    self.active_drive_cycle = None
                    return

            # Meaning we try to end a drive cycle but the program doesn't know any active ones.
            # Should be unreachable, but just in case, clear all drive cycles without end times for this VIN.
            await self._end_active_drive_cycles(session)
            await session.commit()
            self.active_drive_cycle = None

    async def _end_active_drive_cycles(self, session: AsyncSession):
        if not self.vin:
            log.error("Cannot end active drive cycles: VIN not set")
            return

        # This function acts as a cleanup
        # when we need to end the current active drive cycle but don't have a reference to it.
        # + Ideally: Never need to be called
        # + Realistic edge case: When the app crashes while the engine is on, it will miss the engine off event,
        # so the latest drive cycle will remain active.
        #   => Query the latest sample, use its timestamp as the drive cycle's end time.
        # + Catastrophic edge case: Somehow the active drive cycle is not the most recent one.
        #   => TODO: Handling this case is left as an exercise for the reader

        reader = DBReader(session=session)
        if not (
            active_drives := await reader.get_drive_cycles(self.vin, active_only=True)
        ):
            return

        latest_drive = active_drives[0]  # it's sorted by start_time desc

        if latest_sample := await reader.get_latest_sample(self.vin):
            latest_drive.end_time = latest_sample.timestamp
            await self._update_drive_cycle_distance(session, latest_drive)
        else:
            await session.delete(latest_drive)

        for drive in active_drives[1:]:
            await session.delete(drive)

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
        if not self.active_drive_cycle:
            await self.start_drive_cycle()

        sample = LiveSample(vin=self.vin, timestamp=poll.ts, **poll.samples)
        self.samples_buffer.append(sample)

        if len(self.samples_buffer) >= SAMPLES_BATCH_SIZE:
            async with self.session_factory() as session:
                session.add_all(instances=self.samples_buffer)
                self.samples_buffer.clear()

                if self.active_drive_cycle and not self.active_drive_cycle.id:
                    drive = DriveCycle(
                        vin=self.vin,
                        start_time=self.active_drive_cycle.start_time,
                    )
                    session.add(drive)
                    await session.flush()
                    await session.refresh(drive)
                    self.active_drive_cycle.id = drive.id

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
