from datetime import datetime
from typing import Any, List

from fastapi import APIRouter, Request
from contextlib import asynccontextmanager

from sqlalchemy.ext.asyncio import AsyncSession

from db.reader import DBReader

from fastapi.encoders import jsonable_encoder

router = APIRouter()


@asynccontextmanager
async def get_db_reader(request: Request):
    """Helper context manager that yields a DBReader and ensures the AsyncSession is closed."""
    async with request.app.state.db_session_factory() as session:
        yield DBReader(session)


@router.get("/data/sample/{drive_cycle_id}/{fields}")
async def get_sample_data(drive_cycle_id: int, fields: str, request: Request):
    """
    Gets sample data for a given drive cycle, then filters it to only include the given fields.
    Returns a json list of dicts, where each dict represents a sample and only includes the requested fields
    due to the nature of the data, json lists might be very large, so I've paginated the results so that
    you won't get overwhelmed.
    """

    async with get_db_reader(request) as reader:
        samples = await reader.get_samples_in_drive_cycle(drive_cycle_id)

    fields_list = [f.strip() for f in fields.split(",") if f.strip()]

    res = [{f: getattr(s, f, None) for f in fields_list} for s in samples]

    return jsonable_encoder(res)


@router.get("/data/sample/{vin}/{start_time}/{end_time}/{fields}")
async def get_sample_data_by_time_range(vin: str, start_time: str, end_time: str, fields: str, request: Request):

    start_time_dt = datetime.fromisoformat(start_time)
    end_time_dt = datetime.fromisoformat(end_time)

    async with get_db_reader(request) as reader:
        samples = await reader.get_samples_in_time_range(vin=vin, start_time=start_time_dt, end_time=end_time_dt)
    
    fields_list = [f.strip() for f in fields.split(",") if f.strip()]

    res = [{f: getattr(s, f, None) for f in fields_list} for s in samples]

    return jsonable_encoder(res)



@router.get("/data/dtcs/{vin}")
async def get_errors(vin: str, request: Request):
    async with get_db_reader(request) as reader:
        dtcs = await reader.get_dtcs(vin=vin)

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


@router.get("/data/drives_cycles/{n}")
async def get_drive_cycles(n: int, request: Request):
    async with get_db_reader(request) as reader:
        drive_cycles = await reader.get_drive_cycles(limit=n)

    res = [
        {c.name: getattr(dc, c.name, None) for c in dc.__table__.columns}
        for dc in drive_cycles
    ]
    return jsonable_encoder(res)


@router.get("/data/all/vehicles")
async def get_vehicles(request: Request):
    async with get_db_reader(request) as reader:
        vehicles = await reader.get_all_vehicles()

    res = [
        {c.name: getattr(v, c.name, None) for c in v.__table__.columns}
        for v in vehicles
    ]
    return jsonable_encoder(res)


@router.get("/data/all/vehicle_stats/{vin}")
async def get_vehicle_stats(vin: str, request: Request):
    async with get_db_reader(request) as reader:
        stats = await reader.get_vehicle_stats(vin=vin)

    return jsonable_encoder(stats)

@router.get("/data/drive_cycle_stats/{drive_cycle_id}")
async def get_drive_cycle_stats(drive_cycle_id: int, request: Request):
     async with get_db_reader(request) as reader:
         stats = await reader.get_drive_cycle_stats(drive_cycle_id=drive_cycle_id)

     return jsonable_encoder(stats)


@router.post("/dtcs/clear")
async def clear_dtcs(request: Request):
    """Wipes stored DTCs and freeze frames on the ECU.
    The next collector tick will see MIL/count
    change and emit a 'cleared' DTC event into the DB.
    """
    ok = await request.app.state.obd.clear_dtcs()
    return {"cleared": ok}