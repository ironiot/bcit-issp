#!/usr/bin/env bash

set -euo pipefail
cd "$(dirname "$0")"

VENV=.venv
ELM_PORT=35000
ELM_LOG=elm.log
BACKEND_LOG=backend.log

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
    echo "[run] WARNING: BCIT_ISSP_DB_URL not set; backend will fail to start"
    echo "       set it in src/backend/.env (format: user:pass@host:port/dbname)"
fi

# start elm. -d (daemon) ignores -n and forces a pty, so we run it in
# the background instead. process substitution gives it a stdin that
# never EOFs, otherwise the REPL exits the moment we background it.
echo "[run] starting elm on tcp/$ELM_PORT (logs: $ELM_LOG)"
elm -s car -n "$ELM_PORT" >"$ELM_LOG" 2>&1 < <(tail -f /dev/null) &
ELM_PID=$!

cleanup() {
    echo
    echo "[run] stopping elm (pid $ELM_PID)"
    kill "$ELM_PID" 2>/dev/null || true
    wait "$ELM_PID" 2>/dev/null || true
}
trap cleanup EXIT

sleep 1

# backend in foreground
echo "[run] starting backend (logs: $BACKEND_LOG)"
python main.py 2>&1 | tee "$BACKEND_LOG"
