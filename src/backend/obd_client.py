import asyncio
import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone

import obd

OBD_URL = "/dev/pts/5"

log = logging.getLogger("obd_client")


def _mode(cmd):
    return cmd.command[:2]


def utcnow():
    return datetime.now(timezone.utc)


@dataclass
class SamplePoll:
    ts: datetime
    samples: list = field(default_factory=list)  # [(pid, value, unit)]
    mil: bool | None = None  # check-engine light, from mode 01 STATUS PID
    dtc_count: int | None = None  # stored DTC count, from mode 01 STATUS PID


@dataclass
class DTCPoll:
    ts: datetime
    current: dict = field(default_factory=dict)  # code -> description


@dataclass
class FreezePoll:
    ts: datetime
    triggering_code: str | None = None
    samples: list = field(
        default_factory=list
    )  # [(pid, value, unit)] without DTC_ prefix


class OBDClient:
    """Owns the OBD connection and serializes bus access via an asyncio lock.

    python-obd is synchronous and blocking; every query is dispatched through
    asyncio.to_thread while the lock is held, so the event loop stays free and
    only one bus operation is in flight at a time.
    """

    def __init__(self, port: str = OBD_URL):
        self.port = port
        self.conn: obd.OBD | None = None
        self.commands: list = []  # supported mode 01 commands
        self._lock = asyncio.Lock()

    async def connect(self) -> None:
        async with self._lock:
            backoff = 1.0
            while True:
                try:
                    await asyncio.to_thread(self._connect_sync)
                    return
                except ConnectionError as e:
                    log.warning("connect failed: %s; retrying in %.1fs", e, backoff)
                    await asyncio.sleep(backoff)
                    backoff = min(backoff * 2, 30.0)

    def _connect_sync(self) -> None:
        if self.conn is not None and self.conn.is_connected():
            return
        log.info("connecting to %s", self.port)
        self.conn = obd.OBD(self.port, fast=False, timeout=2)
        if not self.conn.is_connected():
            raise ConnectionError(f"failed to open {self.port}")
        log.info("connected, protocol=%s", self.conn.protocol_name())
        self.commands = sorted(
            (c for c in self.conn.supported_commands if _mode(c) == b"01"),
            key=lambda c: c.name,
        )
        log.info(
            "polling %d pids: %s",
            len(self.commands),
            [c.name for c in self.commands],
        )

    async def close(self) -> None:
        async with self._lock:
            if self.conn is not None:
                await asyncio.to_thread(self.conn.close)
                self.conn = None

    def is_connected(self) -> bool:
        return self.conn is not None and self.conn.is_connected()

    async def read_vin(self) -> str | None:
        async with self._lock:
            return await asyncio.to_thread(self._read_vin_sync)

    def _read_vin_sync(self) -> str | None:
        r = self.conn.query(obd.commands.VIN, force=True)
        if r.is_null():
            log.info("VIN is null")
            return None
        return str(r.value)

    async def read_voltage(self) -> float | None:
        async with self._lock:
            return await asyncio.to_thread(self._read_voltage_sync)

    def _read_voltage_sync(self) -> float | None:
        r = self.conn.query(obd.commands.ELM_VOLTAGE, force=True)
        if r.is_null():
            return None
        mag = getattr(r.value, "magnitude", r.value)
        try:
            return float(mag)
        except (TypeError, ValueError):
            return None

    async def read_live(self) -> SamplePoll:
        async with self._lock:
            return await asyncio.to_thread(self._read_live_sync)

    def _read_live_sync(self) -> SamplePoll:
        result = SamplePoll(ts=utcnow())
        for cmd in self.commands:
            r = self.conn.query(cmd)
            if r.is_null():
                continue
            # STATUS (mode 01 PID 0x01) returns a namedtuple.
            # Pull MIL + DTC count off it so the collector can detect changes
            # without a separate poll.
            if cmd.name == "STATUS":
                result.mil = bool(r.value.MIL)
                result.dtc_count = int(r.value.DTC_count)
                continue
            mag = getattr(r.value, "magnitude", r.value)
            unit = getattr(r.value, "units", "")
            try:
                mag = float(mag)
            except (TypeError, ValueError):
                continue
            result.samples.append((cmd.name, mag, str(unit)))
        if result.samples:
            line = "  ".join(f"{n}={v:.2f}{u}" for n, v, u in result.samples)
            log.info("sample %s", line)
        return result

    async def read_dtcs(self) -> DTCPoll:
        async with self._lock:
            return await asyncio.to_thread(self._read_dtcs_sync)

    def _read_dtcs_sync(self) -> DTCPoll:
        result = DTCPoll(ts=utcnow())
        cmd = obd.commands.GET_DTC
        if not self.conn.supports(cmd):
            return result
        r = self.conn.query(cmd)
        if not r.is_null() and r.value:
            for code, desc in r.value:
                log.info("dtc %s %s", code, desc)
                result.current[code] = desc
        return result

    async def clear_dtcs(self) -> bool:
        async with self._lock:
            return await asyncio.to_thread(self._clear_dtcs_sync)

    def _clear_dtcs_sync(self) -> bool:
        r = self.conn.query(obd.commands.CLEAR_DTC)
        return not r.is_null()

    async def read_freeze(self) -> FreezePoll:
        async with self._lock:
            return await asyncio.to_thread(self._read_freeze_sync)

    def _read_freeze_sync(self) -> FreezePoll:
        result = FreezePoll(ts=utcnow())
        frame = self.conn.query(obd.commands.FREEZE_DTC, force=True)
        if not frame.is_null() and frame.value:
            log.info("freeze frame for %s", frame.value)
            if isinstance(frame.value, tuple):
                result.triggering_code = frame.value[0]

        for live_cmd in self.commands:
            dtc_name = "DTC_" + live_cmd.name
            if not obd.commands.has_name(dtc_name):
                continue
            cmd = obd.commands[dtc_name]
            r = self.conn.query(cmd)
            if r.is_null():
                continue
            mag = getattr(r.value, "magnitude", r.value)
            unit = getattr(r.value, "units", "")
            try:
                mag = float(mag)
            except (TypeError, ValueError):
                continue
            result.samples.append((live_cmd.name, mag, str(unit)))
        return result
