# Poltergeist

A Geometry Dash 2.2 server. Python 3.14, FastAPI, MySQL and Redis.

It implements the `/database/*.php` endpoints the game calls: accounts and
login, levels and lists, comments, likes, scores, friends and messages,
songs, map packs and gauntlets, daily, weekly and event levels, chests,
quests and vault rewards. Only the current client protocol is supported and
every request must be logged in.

Moderation runs in game through `!` commands in level comments (rating,
featuring, dailies, bans, roles) and through the admin area of
[rgdps-web](https://github.com/RealistikGDPS/rgdps-web). What an account may
do is decided by dotted permission strings such as `levels.rate` or
`users.ban.*`, granted through roles and per-user overrides.

## Layout

```
app/api/gd      Game endpoints
app/api/health  Internal health check for the container and the website
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

Point the client at `http://<host>/database`. The first administrator is
granted by hand; every later role goes through the website's admin area:

```sql
INSERT INTO user_roles (user_id, role_id) VALUES (<id>, 5);
```

## Events

Major actions (registrations, level uploads and ratings, bans, roles,
settings changes) are announced on Redis Pub/Sub channels named
`poltergeist:*`, each message carrying `"component": "poltergeist"`. The
envelope and the event catalogue are documented in
[poltergeist-core](https://github.com/RealistikGDPS/poltergeist-core#events).

## Development

```bash
uv sync
make lint
```

To pick up a newer poltergeist-core:

```bash
uv lock --upgrade-package poltergeist-core
```
