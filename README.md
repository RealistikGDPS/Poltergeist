# Poltergeist

A Geometry Dash 2.2 server. It speaks only the current protocol, refuses
anything that is not logged in, and puts moderation behind a string-based
permission system that can be reshaped without touching code.

Poltergeist is written for Python 3.14, managed with [uv](https://docs.astral.sh/uv/),
and uses [gdformat](https://pypi.org/project/gdformat/) for every byte that
crosses the wire. Storage is MySQL 9 for records, Redis 8 for sessions,
permissions, rankings and rate limits, and a filesystem volume for level
strings, replays and account saves.

## Running

```bash
for f in configuration/*.example; do cp "$f" "${f%.example}"; done
cp .env.example .env
# Edit configuration/app.env (APP_PUBLIC_URL, APP_ADMIN_API_KEY) and
# configuration/mysql.env (passwords).
make build
make run
```

The game endpoints are served under `/database` and the JSON API under
`/api/v1`. Point a client (for example through a GDPS switcher) at
`http://<host>/database` and set `APP_PUBLIC_URL` to `http://<host>` so
backups and syncs find their way back.

`APP_TRUST_PROXY_HEADERS=true` makes uvicorn honour `X-Forwarded-For` when a
reverse proxy sits in front of the server. Leave it off when the container is
exposed directly.

### Local development

```bash
uv sync
uv run pre-commit install
uv run uvicorn app.main:asgi_app --reload   # with the app.env variables exported
```

`make lint` runs ruff and mypy in strict mode across the codebase.

### Rebuilding the rankings

Redis holds the global leaderboards. They are updated on every stats
submission and can be rebuilt from MySQL at any time:

```bash
make rebuild-leaderboards
# or, over the administration API
curl -X POST -H "X-API-Key: $APP_ADMIN_API_KEY" http://localhost/api/v1/leaderboards/rebuild
```

## Layout

```
app/
├── adapters/    MySQL (asyncmy), Redis, object storage, the official servers
├── resources/   One repository per stored resource; the only place with SQL
├── services/    Business rules; return values, never exceptions
├── api/
│   ├── gd/      The Geometry Dash protocol (/database/*.php)
│   └── v1/      JSON API: health and administration
├── utilities/   Logging, clock, event loop, permission matching
└── settings.py  Flat configuration read from the environment
migrations/      golang-migrate SQL migrations, applied by a one-shot container
```

Dependencies point one way: `api → services → resources → adapters`.
Every request is parsed by gdformat into a typed request, handled by exactly
one service function, and serialised back by gdformat.

## Security model

- Every game endpoint requires `accountID` and `gjp2` and validates them
  before doing anything, except registration, login, `getAccountURL`,
  `getCustomContentURL`, `reportGJLevel` (the client sends no credentials)
  and `getGJAccountComments20` (the client sends the *target's* id in
  `accountID`, so the pair cannot be verified).
- Passwords are stored as bcrypt of the gjp2 the client presents. A verified
  gjp2 is remembered in Redis as a SHA-256 digest for `APP_SESSION_SECONDS`
  so hot requests skip bcrypt. Ten failed attempts lock an account for ten
  minutes.
- Every endpoint checks the secret it expects and rejects clients older than
  `APP_MIN_GAME_VERSION` / `APP_MIN_BINARY_VERSION`.
- Integrity values are verified: level `seed2`, list `seed`, comment `chk`,
  like `chk`, stats `seed2` and the level leaderboard seed. Forged
  submissions are refused.
- Uploads, comments, messages, friend requests, likes, registrations and
  reports are rate limited per account or IP in Redis.
- Demon counts on profiles are recomputed from the demon level ids the client
  reports rather than trusted as sent.

## Permissions

What a user may do is never a column on the user. A permission is a dotted
string such as `levels.rate` or `users.ban.comment`. Roles hold sets of
permissions, users hold roles (optionally expiring) plus per-user allow or
deny overrides, and a deny always wins. `levels.*` grants everything under
`levels`, and `*` grants everything.

The effective set is cached in Redis for five minutes and invalidated on every
role or override change. The permissions the server itself checks are listed
in `app/resources/permissions.py`; roles may hold any string.

Seeded roles:

| Role | Purpose |
|------|---------|
| `default` | Granted on registration: upload, comment, message, submit scores, claim rewards |
| `moderator` | Send levels for rating, coloured comments, moderator badge |
| `elder_moderator` | Rate, feature, schedule dailies, delete, ban from comments/uploads |
| `leaderboard_moderator` | Remove players from the rankings |
| `admin` | `*` |

The in-game moderator badge and the `requestUserAccess` answer are derived
from the `mod.badge.*` permissions.

## In-game commands

A level comment starting with `APP_COMMAND_PREFIX` (`!` by default) is run as a
command instead of being posted, and the reply is shown to the player as a
comment dialog. Every command checks the caller's permissions.

```
!help
!rate <stars> [feature|epic|legendary|mythic]   !unrate
!feature <none|feature|epic|legendary|mythic>   !demon <easy|medium|hard|insane|extreme>
!daily [level]   !weekly [level]   !event [level]
!delete   !unlist   !relist   !lock   !unlock   !move <user>
!ban <user> <account|comment|upload|leaderboard|creator> [days|perm] [reason]
!unban <user> <type>   !colour <r> <g> <b>   !role <user> <role>   !unrole <user> <role>
!whois <user>   !ping
```

## Administration API

Enabled when `APP_ADMIN_API_KEY` is set; every call carries it in the
`X-API-Key` header. Responses are `{"status": <http status>, "data": ...}`.

| Method | Path | Body |
|--------|------|------|
| `POST` | `/api/v1/users/{id}/roles` | `{"role": "admin", "expires_at": null}` |
| `DELETE` | `/api/v1/users/{id}/roles/{role}` | |
| `POST` | `/api/v1/users/{id}/bans` | `{"type": "comment", "days": 7, "reason": "spam"}` |
| `DELETE` | `/api/v1/users/{id}/bans/{type}` | |
| `POST` | `/api/v1/levels/{id}/rating` | `{"stars": 6, "feature": 2, "demon": null}` |
| `POST` | `/api/v1/timely` | `{"type": 0, "level_id": 42}` |
| `POST` | `/api/v1/songs` | `{"name": ..., "artist": ..., "url": ..., "size_bytes": ...}` |
| `POST` | `/api/v1/map-packs` | name, level_ids, stars, coins, difficulty, colours |
| `PUT` | `/api/v1/gauntlets/{id}` | `{"level_ids": [five ids]}` |
| `POST` | `/api/v1/secret-rewards` | key, chest_type, items, max_claims, expires_at |
| `POST` | `/api/v1/leaderboards/rebuild` | |

The first administrator is made with the role endpoint; from then on the
in-game `!role` command works.

## Timely levels, rewards and songs

- Dailies, weeklies and events are a queue per type: scheduling appends an
  entry that starts when the previous one ends (or immediately when nothing
  valid is being served). Events carry a chest whose contents live in
  `timely_level_rewards`.
- Chest cooldowns are `APP_SMALL_CHEST_SECONDS` and `APP_LARGE_CHEST_SECONDS`;
  contents are rolled server side and recorded per claim.
- Three quests are assigned per player per UTC day from the `quests` table,
  one per item type.
- Vault codes (`getGJSecretReward`) come from `secret_rewards` and are
  claimable once per player.
- Newgrounds and music library song metadata is fetched from the official
  servers on first use and cached in MySQL; misses are remembered in Redis for
  ten minutes. Custom songs are added through the administration API.

## Schema notes

`schema.sql` at the repository root was the starting point. Poltergeist's
migration differs in these ways:

- `users.privileges` and `users.mod_level` are gone; roles, permissions and
  overrides replace them.
- `user_credentials` holds one bcrypt of the gjp2 per user. The 2.2 client
  never presents a plaintext password after registration, so a legacy
  plaintext hash could never be verified.
- The `sfx`, `level_songs`, `level_sfx` and `song_artists` tables are gone;
  level song and SFX ids are JSON arrays on `level_data`, because they
  reference the client's libraries which are not mirrored.
- `levels.custom_song_id` is no longer a foreign key so an upload cannot fail
  because the official servers are unreachable.
