# =============================================================================
# FLVS - Makefile fuer Docker Management
# =============================================================================

.PHONY: help build up down logs shell migrate backup restore

help:
	@echo "FLVS - Feuerwehr Lagerverwaltungssystem"
	@echo "======================================="
	@echo ""
	@echo "Verfuegbare Befehle:"
	@echo "  make build      - Docker Images bauen"
	@echo "  make up         - Container starten"
	@echo "  make down       - Container stoppen"
	@echo "  make restart    - Container neu starten"
	@echo "  make logs       - Logs anzeigen"
	@echo "  make shell      - Django Shell oeffnen"
	@echo "  make bash       - Bash im Web-Container"
	@echo "  make migrate    - Datenbank-Migrationen ausfuehren"
	@echo "  make static     - Static Files sammeln"
	@echo "  make backup     - Datenbank-Backup erstellen"
	@echo "  make superuser  - Superuser erstellen"
	@echo "  make test       - Tests ausfuehren"
	@echo "  make clean      - Alle Container und Volumes loeschen"

build:
	docker compose build

up:
	docker compose up -d

up-logs:
	docker compose up

down:
	docker compose down

restart:
	docker compose restart

logs:
	docker compose logs -f

logs-web:
	docker compose logs -f web

shell:
	docker compose exec web python manage.py shell

bash:
	docker compose exec web /bin/bash

migrate:
	docker compose exec web python manage.py migrate

makemigrations:
	docker compose exec web python manage.py makemigrations

static:
	docker compose exec web python manage.py collectstatic --noinput

superuser:
	docker compose exec web python manage.py createsuperuser

backup:
	@mkdir -p docker/backup
	docker compose exec db pg_dump -U flvs flvs | gzip > docker/backup/flvs_backup_$$(date +%Y%m%d_%H%M%S).sql.gz
	@echo "Backup created in docker/backup/"

test:
	docker compose exec web pytest

clean:
	docker compose down -v --remove-orphans
	docker system prune -f

update:
	git pull
	docker compose build
	docker compose up -d
	docker compose exec web python manage.py migrate
	docker compose exec web python manage.py collectstatic --noinput
