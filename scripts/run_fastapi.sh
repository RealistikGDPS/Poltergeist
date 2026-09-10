#!/bin/bash
set -euo pipefail

echo "Starting Poltergeist..."

UVICORN_ARGS=(
    "--host" "${APP_HTTP_HOST:=0.0.0.0}"
    "--port" "${APP_HTTP_PORT:=80}"
    "--no-server-header"
)

if [ "${APP_TRUST_PROXY_HEADERS:-false}" = "true" ]; then
    UVICORN_ARGS+=("--proxy-headers" "--forwarded-allow-ips" "*")
fi

if [ "${APP_DEV_MODE:-false}" = "true" ]; then
    echo "Development mode enabled."
    UVICORN_ARGS+=("--reload")
fi

exec uv run --no-sync uvicorn app.main:asgi_app "${UVICORN_ARGS[@]}"
