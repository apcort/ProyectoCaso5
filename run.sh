#!/usr/bin/env bash
cd "$(dirname "$0")" || exit 1
if [ -d .venv ]; then
    source .venv/bin/activate
fi
exec python3 main.py "$@"