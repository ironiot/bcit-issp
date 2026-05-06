from typing import Any, List

from fastapi import FastAPI, Request

app = FastAPI()


@app.get("/data/sample/{drive_cycle_id}/{fields}/{vin}")
def get_sample_data(drive_cycle_id: int, fields: List[Any], vin: str):

    res = get_data_from_db(drive_cycle_id, fields, vin)

    return res


@app.get("/data/dtcs/{vin}")
def get_errors(vin: str):

    res = get_errors_from_db(vin)

    return res


@app.get("/data/drives_cycles/{n}")
def get_drive_cycles(n: int):

    res = get_drive_cycles_from_db(n)

    return res


@app.get("/data/all/vehicles")
def get_vehicles():

    res = get_vehicles_from_db()

    return res


@router.post("/dtcs/clear")
async def clear_dtcs(request: Request):
    """Wipes stored DTCs and freeze frames on the ECU.
    The next collector tick will see MIL/count
    change and emit a 'cleared' DTC event into the DB.
    """
    ok = await request.app.state.obd.clear_dtcs()
    return {"cleared": ok}



def get_data_from_db(drive_cycle_id: int, fields: List[Any], vin: str):
    pass


def get_errors_from_db(vin: str):
    pass


def get_drive_cycles_from_db(n: int):
    pass


def get_vehicles_from_db():
    pass
