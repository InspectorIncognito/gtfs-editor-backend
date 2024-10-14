# Windows
ifeq ($(OS),Window_NT)
	TEST = docker compose -p gtfs-editor-test -f docker\docker-compose.yml --profile test
	COMPOSE_DEV = docker compose -p gtfseditor-backend-dev -f docker\docker-compose.yml -f docker\docker-compose-dev.yml --profile dev
	COMPOSE_PROD = docker compose -p emov-backend-prod -f docker\docker-compose.yml --profile prod
	MANAGE=python backend\manage.py
# Linux
else
	TEST = docker compose -p gtfs-editor-test -f docker/docker-compose.yml --profile test
	COMPOSE_DEV = docker compose -p gtfseditor-backend-dev -f docker/docker-compose.yml -f docker/docker-compose-dev.yml --profile dev
	COMPOSE_PROD = docker compose -p gtfseditor-backend-prod -f docker/docker-compose.yml --profile prod
	COMPOSE_CERT = docker compose -p gtfseditor-backend-prod -f docker/docker-compose.yml -f docker/docker-compose-certbot.yml --profile certbot
	MANAGE=python backend/manage.py
endif
PIP=pip install -r requirements-prod.txt


test:
	$(TEST) build
	$(TEST) up --abort-on-container-exit
test_down:
	$(TEST) down
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

prod_up:
	@aws ecr get-login-password --region us-east-2 | docker login --username AWS --password-stdin 992591977826.dkr.ecr.us-east-2.amazonaws.com
	@$(COMPOSE_PROD) pull
	@$(COMPOSE_PROD) up -d
prod_up_cert:
	$(COMPOSE_PROD) up -d
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
