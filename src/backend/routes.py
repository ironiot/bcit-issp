from typing import Any, List

from fastapi import FastAPI

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


def get_data_from_db(drive_cycle_id: int, fields: List[Any], vin: str):
    pass


def get_errors_from_db(vin: str):
    pass


def get_drive_cycles_from_db(n: int):
    pass


def get_vehicles_from_db():
    pass
