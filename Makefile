.PHONY: up down status test

up:
	docker compose up -d

down:
	docker compose down

status:
	docker compose ps

test:
	docker build -t settle-api:test -f app/Dockerfile .
	docker run --rm settle-api:test pytest -q