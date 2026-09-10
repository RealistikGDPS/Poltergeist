#!/usr/bin/make
build:
	docker compose build

run:
	docker compose up app

run-d:
	docker compose up -d app

stop:
	docker compose down

logs:
	docker compose logs -f app

lint:
	uv run pre-commit run --all-files

rebuild-leaderboards:
	docker compose --profile tools run --rm leaderboards
