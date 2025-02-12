# Windows
ifeq ($(OS),Window_NT)
	DOCKER_COMPOSE = docker compose -p gtfseditor-backend-dev
# Linux
else
	DOCKER_COMPOSE = docker compose -p gtfseditor-backend-dev
endif

COMPOSE_PROD = $(DOCKER_COMPOSE) -f docker\docker-compose.yml --profile prod
COMPOSE_DEV = $(DOCKER_COMPOSE) -f docker\docker-compose.yml -f docker\docker-compose.dev.yml --profile dev
COMPOSE_TEST = $(DOCKER_COMPOSE) -f docker\docker-compose.yml -f docker\docker-compose.dev.yml --profile test
MANAGE = python manage.py
PIP = pip install -r requirements-prod.txt


test:
	$(COMPOSE_TEST) build
	$(COMPOSE_TEST) up --abort-on-container-exit
test_down:
	$(COMPOSE_TEST) down
install_local:
	$(PIP) -r requirements-dev.txt
config_env:
	@if [ ! -f .env ]; then \
		cp docker/docker_env .env; \
 	fi
	@sed -i 's/DB_HOST=db/DB_HOST=localhost/' .env
	@sed -i 's/DB_PORT=5432/DB_PORT=5431/' .env
	@sed -i 's/REDIS_HOST=cache/REDIS_HOST=localhost/' .env
	@sed -i 's/TESTING=False/TESTING=True/' .env
	@sed -i 's/DEBUG=False/DEBUG=True/' .env
	@sed -i 's/SERVER_MODE=.*/SERVER_MODE=test/' .env

build:
	$(COMPOSE_DEV) build

rebuild:
	$(COMPOSE_DEV) build --no-cache

up:
	$(COMPOSE_DEV) up

down:
	$(COMPOSE_DEV) down

db:
	$(COMPOSE_DEV) --profile dev up db
prod_build:
	$(COMPOSE_PROD) build
prod_up:
	@$(COMPOSE_PROD) up -d
build_nginx:
	$(COMPOSE_DEV) build nginx --no-cache
	# if it's running, restart it
	$(COMPOSE_DEV) restart nginx
prod_down:
	$(COMPOSE_PROD) down
prod_superuser:
	$(COMPOSE_PROD) exec -ti web python /app/backend/manage.py createsuperuser
create_superuser:
	$(MANAGE) createsuperuser
migrate:
	$(MANAGE) makemigrations
	$(MANAGE) migrate
container_bash:
	$(COMPOSE_DEV) exec $(service) /bin/bash
emit_certificate:
	$(COMPOSE_CERT) up --abort-on-container-exit
container_bash_prod:
	$(COMPOSE_PROD) exec $(service) /bin/bash
