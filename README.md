# Poltergeist

A Geometry Dash 2.2 server written in Python 3.14 with FastAPI. It speaks only
the current game protocol, requires a login for everything, and keeps
moderation behind a flexible string-based permission system.

## Highlights

- Every request and response goes through [gdformat](https://pypi.org/project/gdformat/),
  so the server never touches the wire format itself.
- Nothing works unauthenticated. Passwords are bcrypt hashed, verified logins
  are cached in Redis, and every client integrity value is checked.
- Permissions are dotted strings (`levels.rate`, `users.ban.*`, `*`) granted
  through roles and per-user overrides. Roles can be reshaped without code.
- Moderation happens in game through `!` commands in level comments
  (rating, featuring, dailies, bans, roles) or through a small JSON
  administration API.
- Global leaderboards live in Redis sorted sets; chests, quests, vault codes,
  dailies, weeklies and events are all served.
- MySQL 9 for records, Redis 8 for caches and rankings, a volume for level
  strings, replays and saves. Everything runs from one `docker compose up`.

## Running

```bash
for f in configuration/*.example; do cp "$f" "${f%.example}"; done
cp .env.example .env
# Set APP_PUBLIC_URL, APP_ADMIN_API_KEY, the MySQL passwords and GITHUB_TOKEN.
make build
make run
```

`GITHUB_TOKEN` must be able to read the private
[poltergeist-core](https://github.com/RealistikGDPS/poltergeist-core)
repository; the image build passes it to `uv sync` as a build secret and it
is not stored in the image.

Point the client at `http://<host>/database`. The bundled nginx also routes
`/panel` to the separate control room, when that is running on the same
Docker network. The JSON API lives under
`/api/v1`; create the first administrator with it:

```bash
curl -X POST -H "X-API-Key: $APP_ADMIN_API_KEY" -H "Content-Type: application/json" \
  -d '{"role":"admin"}' http://<host>/api/v1/users/<id>/roles
```

## Development

```bash
uv sync
make lint   # ruff and strict mypy
```

The code follows the layered layout `api → services → resources → adapters`:
transport, business rules, queries and external systems, each importing only
the layer to its right. Expected failures are return values, never exceptions.

Only the transport layer (`app/api`) and the entry point live here. The
services, resources, adapters and utilities are the
[poltergeist-core](https://github.com/RealistikGDPS/poltergeist-core)
library, shared with the control room and consumed from Git. Change shared
logic there, then pull the new revision in:

```bash
uv lock --upgrade-package poltergeist-core
```
