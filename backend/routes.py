from contextlib import asynccontextmanager
from datetime import datetime, timezone
from uuid import UUID

from db.model import Dtc
from db.reader import DBReader
from collector import ENGINE_ON_VOLTAGE
from fastapi import APIRouter, HTTPException, Request
from fastapi.encoders import jsonable_encoder
from sqlalchemy import update

router = APIRouter()


@asynccontextmanager
async def get_db_reader(request: Request):
    """Helper context manager that yields a DBReader and ensures the AsyncSession is closed."""
    async with request.app.state.db_session_factory() as session:
        yield DBReader(session)


@router.get("/data/samples/drive_cycle/{id}")
async def get_sample_data(id: UUID, request: Request, fields: str = ""):
    """
    Gets sample data for a given drive cycle, then filters it to only include the given fields.
    Returns a json list of dicts, where each dict represents a sample and only includes the requested fields
    due to the nature of the data, json lists might be very large, so I've paginated the results so that
    you won't get overwhelmed.
    """

    async with get_db_reader(request) as reader:
        samples = await reader.get_samples_in_drive_cycle(id)

    if not fields:
        res = [
            {c.name: getattr(s, c.name, None) for c in s.__table__.columns}
            for s in samples
        ]
        return jsonable_encoder(res)

    fields_list = ["timestamp"] + [f.strip() for f in fields.split(",") if f.strip()]
    filtered_res = [{f: getattr(s, f, None) for f in fields_list} for s in samples]
    return jsonable_encoder(filtered_res)


@router.get("/data/samples/vin/{vin}")
async def get_sample_data_by_time_range(
    vin: str,
    request: Request,
    start_time: str | None = None,
    end_time: str | None = None,
    fields: str = "",
):
    async with get_db_reader(request) as reader:
        samples = await reader.get_samples_in_time_range(
            vin,
            start_time=datetime.fromisoformat(start_time) if start_time else None,
            end_time=datetime.fromisoformat(end_time) if end_time else None,
        )

    if not fields:
        res = [
            {c.name: getattr(s, c.name, None) for c in s.__table__.columns}
            for s in samples
        ]
        return jsonable_encoder(res)

    fields_list = ["timestamp"] + [f.strip() for f in fields.split(",") if f.strip()]
    filtered_res = [{f: getattr(s, f, None) for f in fields_list} for s in samples]
    return jsonable_encoder(filtered_res)


@router.get("/data/samples/latest/{vin}")
async def get_latest_sample(
    vin: str,
    request: Request,
    fields: str = "",
):
    async with get_db_reader(request) as reader:
        latest_sample = await reader.get_latest_sample(vin)
    if not latest_sample:
        raise HTTPException(
            status_code=404, detail="No sample found for the given VIN."
        )

    if not fields:
        return jsonable_encoder({
            c.name: getattr(latest_sample, c.name, None)
            for c in latest_sample.__table__.columns
        })

    fields_list = ["timestamp"] + [f.strip() for f in fields.split(",") if f.strip()]
    return jsonable_encoder({f: getattr(latest_sample, f, None) for f in fields_list})


@router.get("/data/dtcs/{vin}")
async def get_errors(
    vin: str,
    request: Request,
    start_time: datetime | None = None,
    end_time: datetime | None = None,
    active_only: bool = False,
    code: str | None = None,
):
    async with get_db_reader(request) as reader:
        dtcs = await reader.get_dtcs(
            vin,
            start_time=start_time,
            end_time=end_time,
            active_only=active_only,
            code=code,
        )

    res = []
    for dtc in dtcs:
        row = {c.name: getattr(dtc, c.name, None) for c in dtc.__table__.columns}

        freeze = getattr(dtc, "freeze_frame", None)
        row["freeze_frame"] = (
            {c.name: getattr(freeze, c.name, None) for c in freeze.__table__.columns}
            if freeze
            else None
        )
        res.append(row)

    return jsonable_encoder(res)


@router.get("/data/drives_cycles/{vin}")
async def get_drive_cycles(
    request: Request,
    vin: str,
    start_time: datetime | None = None,
    end_time: datetime | None = None,
    active_only: bool = False,
):
    async with get_db_reader(request) as reader:
        drive_cycles = await reader.get_drive_cycles(
            vin,
            start_time=start_time,
            end_time=end_time,
            active_only=active_only,
        )

    res = [
        {c.name: getattr(dc, c.name, None) for c in dc.__table__.columns}
        for dc in drive_cycles
    ]
    return jsonable_encoder(res)


@router.get("/data/vehicles")
async def get_vehicles(request: Request):
    async with get_db_reader(request) as reader:
        return await reader.get_vehicles()


@router.get("/data/drive_cycle_stats/{drive_cycle_id}")
async def get_drive_cycle_stats(drive_cycle_id: UUID, request: Request):
    async with get_db_reader(request) as reader:
        stats = await reader.get_drive_cycle_stats(drive_cycle_id=drive_cycle_id)

    return jsonable_encoder(stats)


@router.post("/dtcs/clear")
async def clear_dtcs(request: Request):
    """Wipes stored DTCs and freeze frames on the ECU.
    The next collector tick will see MIL/count
    change and emit a 'cleared' DTC event into the DB.
    """
    # Most ECUs only honor Mode 04 with the engine off. Use the same voltage
    # threshold the collector uses to decide engine-on, and refuse otherwise
    # so the user gets a clear error instead of a silent NACK.
    obd_client = request.app.state.obd
    voltage = await obd_client.read_voltage()
    if voltage is not None and voltage > ENGINE_ON_VOLTAGE:
        raise HTTPException(
            status_code=409,
            detail=f"Engine appears to be running (voltage {voltage:.1f}V > {ENGINE_ON_VOLTAGE}V). Turn the engine off and retry.",
        )
    ok = await obd_client.clear_dtcs()
    return {"cleared": ok}


@router.post("/dtcs/clear/db/{vin}")
async def clear_dtcs_db(vin: str, request: Request):
    # Demo-only: marks all active DTCs for the VIN as cleared by writing
    # cleared_at directly.
    async with request.app.state.db_session_factory() as session:
        result = await session.execute(
            update(Dtc)
            .where(Dtc.vin == vin, Dtc.cleared_at.is_(None))
            .values(cleared_at=datetime.now(timezone.utc))
        )
        await session.commit()
    return {"cleared": result.rowcount}
