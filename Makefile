PHONY: install
install:
	poetry install --

PHONY: format
format:
	black --line-length 120 .
	isort --atomic .

PHONY: run
run:
	uvicorn app.main:app --reload

requirements.txt:
	poetry export -f requirements.txt --output requirements.txt

# Running with docker
PHONY: build
build:
	docker-compose -f docker-compose.dev.yml build

PHONY: compose-up
compose-up: build
	@echo "\n NOTE: You will need to run 'make build-frontend' in another shell for frontend changes to take effect\n"
	docker-compose -f docker-compose.dev.yml up -d

PHONY: compose-down
compose-down:
	docker-compose -f docker-compose.dev.yml down --remove-orphans

# Docker Misc.
PHONY: cbash
cbash:
	docker exec -it $$(docker ps -aqf "name=automated-accounts-payable_app_1") /bin/bash

PHONY: logs
logs:
	docker logs -f $$(docker ps -aqf "name=automated-accounts-payable_app_1")

# DB management
PHONY: upgrade-db
upgrade-db: compose-up
	alembic upgrade head

PHONY: revision-auto
revision-auto:
	alembic revision --autogenerate

# Deployment
release.zip:
	zip -r "release-$$(date +"%Y-%m-%d-%H-%M-%S").zip" .

# Frontend TailwindCSS Studd
PHONY: build-frontend
build-frontend:
	npx tailwindcss -i app/frontend/src/input.css -o app/frontend/static/output.css --watch --config=app/frontend/tailwind.config.js
