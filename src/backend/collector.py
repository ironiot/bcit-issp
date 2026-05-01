import argparse
import logging
import signal
import time

from obd import OBD, OBDCommand, commands

OBD_URL = "/dev/pts/1"  # PTY printed by `python3 -m elm`

POLL_HZ = 5
DTC_PERIOD = 30.0  # seconds between DTC scans when --dtcs is on
PIDS = ["RPM", "SPEED", "COOLANT_TEMP", "THROTTLE_POS", "INTAKE_TEMP", "MAF"]
INFO_PIDS = ["VIN", "CALIBRATION_ID", "CVN", "ECU_NAME"]
FREEZE_PIDS = [
    "DTC_RPM",
    "DTC_SPEED",
    "DTC_COOLANT_TEMP",
    "DTC_THROTTLE_POS",
    "DTC_ENGINE_LOAD",
]
VEHICLE = "car1"

log = logging.getLogger("collector")


class Collector:
    def __init__(self, port=OBD_URL, want_vin=False, want_dtcs=False):
        self.running = True
        self.port = port
        self.want_vin = want_vin
        self.want_dtcs = want_dtcs
        self.conn: None | OBD = None
        self.commands = []
        self.last_dtcs = set()

    def connect(self):
        # open connection handle to the OBD_URL
        while self.running:
            log.info("connecting to %s", self.port)
            self.conn = OBD(self.port, fast=False, timeout=2)
            if self.conn.is_connected():
                log.info("connected, protocol=%s", self.conn.protocol_name())
                wanted: list[OBDCommand] = [
                    commands[p] for p in PIDS if commands.has_name(p)
                ]  # type: ignore
                self.commands = [c for c in wanted if self.conn.supports(c)]
                log.info(
                    "polling %d pids: %s",
                    len(self.commands),
                    [c.name for c in self.commands],
                )
                if self.want_vin:
                    self.poll_mode_09()  # get vehicle data at start if desired
                return
            log.warning("connect failed, retrying in 5s")
            time.sleep(5)

    def poll_mode_09(self):
        if not self.conn:
            return

        # this is the vehicle identity data, should only need to query once
        for name in INFO_PIDS:
            if not commands.has_name(name):
                continue
            cmd = commands[name]
            if not self.conn.supports(cmd):
                continue
            r = self.conn.query(cmd)
            if r.is_null():
                continue
            log.info("info %s=%s", name, r.value)

    def poll_mode_03(self):
        if not self.conn:
            return

        # this mode contains the dtc data, error codes + ref to mode 2 snapshot
        cmd = commands["GET_DTC"]
        if not self.conn.supports(cmd):
            log.info("dtcs unsupported by ECU")
            self.want_dtcs = False
            return
        r = self.conn.query(cmd)
        current = set()
        if not r.is_null() and r.value:
            for code, desc in r.value:
                log.info("dtc %s %s", code, desc)
                current.add(code)
        else:
            log.info("dtcs none")

        # this only gets the DTC snapshot data if there are new error codes
        new_codes = current - self.last_dtcs
        self.last_dtcs = current
        if new_codes:
            log.info("new dtcs %s, fetching freeze frame", sorted(new_codes))
            self.poll_mode_02()

    def poll_mode_01(self):
        if not self.conn:
            return

        # this mode is the 'live' vehicle data, like speed rpm etc...
        samples = []
        for cmd in self.commands:
            r = self.conn.query(cmd)
            if r.is_null():
                continue
            mag = getattr(r.value, "magnitude", r.value)
            unit = getattr(r.value, "units", "")
            try:
                mag = float(mag)  # type: ignore
            except (TypeError, ValueError):
                continue
            samples.append((cmd.name, mag, unit))
        if samples:
            line = "  ".join(f"{n}={v:.2f}{u}" for n, v, u in samples)
            log.info("sample %s", line)

    def poll_mode_02(self):
        # this is the snapshot of a vehicle at the time of a DTC, same as mode 1 but with DTC_ prefix

        if not self.conn:
            return

        frame = self.conn.query(commands["FREEZE_DTC"])
        if not frame.is_null() and frame.value:
            log.info("freeze frame for %s", frame.value)
        for name in FREEZE_PIDS:
            if not commands.has_name(name):
                continue
            cmd = commands[name]
            if not self.conn.supports(cmd):
                continue
            r = self.conn.query(cmd)
            if r.is_null():
                continue
            log.info("freeze %s=%s", name, r.value)

    def run(self):
        # main driver, connects and runs polls at specified frequencies
        self.connect()
        period = 1.0 / POLL_HZ
        # ticks because we do not ever want to go backwards in time
        next_tick = time.monotonic()
        next_dtc = time.monotonic()
        while self.running and self.conn:
            try:
                if not self.conn.is_connected():
                    log.warning("lost connection, reconnecting")
                    self.connect()
                self.poll_mode_01()  # main data is here
                if self.want_dtcs and time.monotonic() >= next_dtc:
                    self.poll_mode_03()  # error data
                    next_dtc = time.monotonic() + DTC_PERIOD
            except Exception:
                log.exception("poll failed")
                time.sleep(1)
            next_tick += period
            sleep = next_tick - time.monotonic()
            if sleep > 0:
                time.sleep(sleep)
            else:
                next_tick = time.monotonic()

    def stop(self, *_):
        # close connection
        log.info("shutting down")
        self.running = False
        if self.conn:
            self.conn.close()


def main():
    # args
    p = argparse.ArgumentParser()
    p.add_argument(
        "--port", default=OBD_URL, help=f"OBD port path or URL (default: {OBD_URL})"
    )
    p.add_argument(
        "--vin",
        action="store_true",
        help="query VIN and Mode 09 vehicle info once at connect",
    )
    p.add_argument(
        "--dtcs", action="store_true", help=f"poll stored DTCs every {DTC_PERIOD:.0f}s"
    )
    args = p.parse_args()

    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s"
    )

    # run
    c = Collector(port=args.port, want_vin=args.vin, want_dtcs=args.dtcs)
    signal.signal(signal.SIGINT, c.stop)
    signal.signal(signal.SIGTERM, c.stop)
    c.run()


if __name__ == "__main__":
    main()
