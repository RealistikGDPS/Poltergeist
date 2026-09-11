# Poltergeist

A Geometry Dash 2.2 server. Python 3.14, FastAPI, MySQL and Redis.

It implements the `/database/*.php` endpoints the game calls: accounts and
login, levels and lists, comments, likes, scores, friends and messages,
songs, map packs and gauntlets, daily, weekly and event levels, chests,
quests and vault rewards. Only the current client protocol is supported and
every request must be logged in.

Moderation runs in game through `!` commands in level comments (rating,
featuring, dailies, bans, roles) and through a small JSON API under
`/api/v1`. What an account may do is decided by dotted permission strings
such as `levels.rate` or `users.ban.*`, granted through roles and per-user
overrides.

## Layout

```
app/api/gd      Game endpoints
app/api/v1      JSON administration API and health check
app/main.py     Entry point, selected by APP_COMPONENT
scripts/        Container start scripts
configuration/  Example environment files
```

The services, repositories and adapters live in
[poltergeist-core](https://github.com/RealistikGDPS/poltergeist-core).

## Running

The `Dockerfile` builds the image. `configuration/app.env.example` lists the
variables the server reads and `configuration/mysql.env.example` the database
credentials. `APP_COMPONENT=fastapi` serves the game;
`APP_COMPONENT=rebuild_leaderboards` recomputes the Redis rankings and exits.

Point the client at `http://<host>/database`. To create the first
administrator:

```bash
curl -X POST -H "X-API-Key: $APP_ADMIN_API_KEY" -H "Content-Type: application/json" \
  -d '{"role":"admin"}' http://<host>/api/v1/users/<id>/roles
```

## Development

```bash
uv sync
make lint
```

To pick up a newer poltergeist-core:

```bash
uv lock --upgrade-package poltergeist-core
```
