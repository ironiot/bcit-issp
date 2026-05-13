# Cloud-OBD2
Cloud-OBD2 is a web application that collects and stores OBD2 data from vehicles
with data persistence beyond the current session,
allowing users to obtain diagnostic data (i.e. metrics and errors) from
past data collection.

## Requirements
To run the application, the following are required:
* Python
* Node.js (and `npm`)
* PostgreSQL

## Installation
To install the application, clone this repository.
Before running the app, go to the `backend` directory and setup the 
database by running
```bash
python db/model.py
```
`python` in this case may be called differently (e.g. `py`, `python3`, etc.),
so run with the appropriate command.
Then, we can setup and run the backend using
```bash
export BCIT_ISSP_DB_URL=[username]@localhost:5432/postgres
./run.sh
```
where we setup the URL for the target database of the diagnostic data.
This target has to have the same schema setup of [db-schema](docs/schema.png),
which `python db/model.py` initialises.

As for the frontend, go to the `frontend` directory and run
```bash
npm install
npm run dev
```

## TODO
* Test car voltage for engine on and off states to
  verify the accuracy of emulator data.
* Add an argument to `run.sh` specifying the ELM device to listen to.
* Add the `.env` to `model.py` and add `.env.example` for easy setup.

