#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")"

PORT="${PORT:-8080}"

exec gunicorn albercas_semiolimpicas.wsgi:application \
  --config gunicorn.conf.py \
  --bind "0.0.0.0:${PORT}"
