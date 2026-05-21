# Iron-OBD2
Iron-OBD2 is a web application that collects and 
stores OBD2 data from vehicles with data persistence 
beyond the current session, allowing users to obtain 
diagnostic data (i.e. metrics and errors) from
past data collection.

Currently, OBD-II dashboards lack support for 
automatic storage of past collections and only 
displays the live vehicle metrics and errors.
Other systems like Tesla's Diagnostic Software
is locked behind a paywall and may only
profitable if used for a business, while 
the pricing can be a burden for individuals. 

Iron-OBD2 fills this gap, and due to its
open-source nature, available for everybody
with no fees attached.

## Features
* Storage of past drive cycle metrics
* Time-domain graphs
* See data from multiple vehicles
* Show errors associated with metrics and vice versa 

## Requirements
To run the application, the following are required:
* a UNIX-like machine (Linux, MacOS)
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
The terminal will print a URL (https://localhost:5173 usually)
where it hosts the frontend.

## TODO
* Test car voltage for engine on and off states to
  verify the accuracy of emulator data.
* Add an argument to `run.sh` specifying the ELM device to listen to.
* Add the `.env` to `model.py` and add `.env.example` for easy setup.

