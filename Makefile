.PHONY: dev test lint migrate backup

dev:
	docker compose -f infra/docker-compose.yml up -d
	uvicorn researchcache.main:app --reload --host 0.0.0.0 --port 8000

test:
	pytest tests/

lint:
	ruff check . && ruff format --check .

migrate:
	alembic upgrade head

backup:
	pg_dump "$$(grep ^DATABASE_URL .env | cut -d= -f2-)" > backup_$$(date +%Y%m%d_%H%M%S).sql
