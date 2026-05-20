#!/usr/bin/env bash

set -euo pipefail
cd "$(dirname "$0")"

VENV=.venv

# instance 1 (car scenario)
ELM1_SCENARIO=car
ELM1_PORT=35000
ELM1_LOG=elm1.log
BACKEND1_LOG=backend1.log
BACKEND1_PORT=8000
VIN1=WP0ZZZ99ZTS390001

# instance 2 (mt05 scenario)
ELM2_SCENARIO=mt05
ELM2_PORT=35001
ELM2_LOG=elm2.log
BACKEND2_LOG=backend2.log
BACKEND2_PORT=8001
VIN2=JM3KFBDM5K0123456

# frontend
FRONTEND_DIR=../frontend
FRONTEND_PORT=5173
FRONTEND_LOG=frontend.log

# kill anything holding ports from a prior (possibly crashed) run so the
# script is safe to re-invoke. lsof -ti prints just pids; xargs -r is a
# no-op when nothing's listening.
free_port() {
    local port=$1
    local pids
    pids=$(lsof -ti:"$port" 2>/dev/null || true)
    if [[ -n "$pids" ]]; then
        echo "[run] freeing port $port (killing $pids)"
        # shellcheck disable=SC2086
        kill $pids 2>/dev/null || true
        sleep 0.3
        pids=$(lsof -ti:"$port" 2>/dev/null || true)
        if [[ -n "$pids" ]]; then
            # shellcheck disable=SC2086
            kill -9 $pids 2>/dev/null || true
        fi
    fi
}

echo "[run] freeing any ports held by a prior run"
free_port "$ELM1_PORT"
free_port "$ELM2_PORT"
free_port "$BACKEND1_PORT"
free_port "$BACKEND2_PORT"
free_port "$FRONTEND_PORT"

# postgres
if ! pg_isready -h localhost -p 5432 -q 2>/dev/null; then
    echo "[run] postgres not running, starting via systemctl (will prompt for sudo)"
    sudo systemctl start postgresql
    # wait up to 10s for it to come up
    for _ in {1..20}; do
        pg_isready -h localhost -p 5432 -q 2>/dev/null && break
        sleep 0.5
    done
    if ! pg_isready -h localhost -p 5432 -q 2>/dev/null; then
        echo "[run] ERROR: postgres failed to start"
        exit 1
    fi
fi

# venv
if [[ ! -d "$VENV" ]]; then
    echo "[run] creating $VENV"
    python3 -m venv "$VENV"
fi
# shellcheck disable=SC1091
source "$VENV/bin/activate"

# python deps + ELM327-emulator hotfix
echo "[run] installing deps"
pip install -q --upgrade pip
pip install -q "setuptools<81" wheel
pip install -q --no-build-isolation ELM327-emulator
pip install -q -r requirements.txt

# load .env
if [[ -f .env ]]; then
    set -a
    # shellcheck disable=SC1091
    source .env
    set +a
fi

if [[ -z "${BCIT_ISSP_DB_URL:-}" ]]; then
    echo "[run] WARNING: BCIT_ISSP_DB_URL not set; backends will fail to start"
    echo "       set it in src/backend/.env (format: user:pass@host:port/dbname)"
fi

# install frontend deps if missing
if [[ ! -d "$FRONTEND_DIR/node_modules" ]]; then
    echo "[run] installing frontend deps"
    ( cd "$FRONTEND_DIR" && npm install --silent )
fi

PIDS=()

cleanup() {
    echo
    echo "[run] stopping all instances (pids: ${PIDS[*]:-none})"
    for pid in "${PIDS[@]:-}"; do
        kill "$pid" 2>/dev/null || true
    done
    for pid in "${PIDS[@]:-}"; do
        wait "$pid" 2>/dev/null || true
    done
}
trap cleanup EXIT

# spawn an elm emulator in the background. -d (daemon) ignores -n and
# forces a pty, so we run it backgrounded with process substitution as
# stdin so the REPL doesn't EOF and exit.
start_elm() {
    local scenario=$1 port=$2 log=$3
    echo "[run] starting elm scenario=$scenario on tcp/$port (logs: $log)"
    elm -s "$scenario" -n "$port" >"$log" 2>&1 < <(tail -f /dev/null) &
    PIDS+=("$!")
}

start_backend() {
    local obd_port=$1 http_port=$2 vin=$3 log=$4
    echo "[run] starting backend http=$http_port vin=$vin (logs: $log)"
    OBD_URL="socket://127.0.0.1:${obd_port}" \
    HTTP_PORT="$http_port" \
    OBD_VIN_OVERRIDE="$vin" \
        python main.py >"$log" 2>&1 &
    PIDS+=("$!")
}

start_frontend() {
    echo "[run] starting frontend on tcp/$FRONTEND_PORT (logs: $FRONTEND_LOG)"
    ( cd "$FRONTEND_DIR" && npm run dev -- --port "$FRONTEND_PORT" --host ) \
        >"$FRONTEND_LOG" 2>&1 &
    PIDS+=("$!")
}

start_elm "$ELM1_SCENARIO" "$ELM1_PORT" "$ELM1_LOG"
start_elm "$ELM2_SCENARIO" "$ELM2_PORT" "$ELM2_LOG"

sleep 1

start_backend "$ELM1_PORT" "$BACKEND1_PORT" "$VIN1" "$BACKEND1_LOG"
start_backend "$ELM2_PORT" "$BACKEND2_PORT" "$VIN2" "$BACKEND2_LOG"

start_frontend

echo "[run] all processes started; ctrl-c to stop"
echo "      backend1: http://localhost:${BACKEND1_PORT}  vin=${VIN1}"
echo "      backend2: http://localhost:${BACKEND2_PORT}  vin=${VIN2}"
echo "      frontend: http://localhost:${FRONTEND_PORT}"

# block until any child exits, then cleanup kills the rest
wait -n
