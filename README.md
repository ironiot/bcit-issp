# Cloud-OBD2
Cloud-OBD2

## Requirements
To run the application, the following are needed:
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
Then, we can run the backend using
```bash
export BCIT_ISSP_DB_URL=[username]@localhost:5432/postgres
./run.sh
```
where we setup the URL for the target of the diagnostic data.

As for the frontend, go to the `frontend` directory and run
```bash
npm install
npm run dev
```

## DB Schema

[db-schema](docs/schema.png)

## TODO
* Test car voltage for engine on and of states to
  verify the accuracy of emulator data 

