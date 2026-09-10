#!/bin/bash
set -euo pipefail

case "${APP_COMPONENT:-}" in
  fastapi)
    exec /app/scripts/run_fastapi.sh
    ;;
  rebuild_leaderboards)
    exec uv run --no-sync python -m app.main
    ;;
  *)
    echo "Bootstrap - Unknown APP_COMPONENT: ${APP_COMPONENT:-<unset>}"
    exit 1
    ;;
esac
