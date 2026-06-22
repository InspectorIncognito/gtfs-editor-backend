# ==============================================================================
# Makefile para GTFS Editor Backend
# ==============================================================================
# Este archivo centraliza los comandos de Docker Compose para diferentes
# entornos (desarrollo, producción, pruebas) y tareas de mantenimiento.
#
# Requisitos:
#   - Docker y Docker Compose
#   - Make (GNU Make)
#
# Uso:
#   make <comando> [service=<nombre_servicio>]
#
# Ejemplos:
#   make up                         # Levanta el entorno de desarrollo
#   make container_bash             # Abre shell en el contenedor 'web' (por defecto)
#   make container_bash service=db  # Abre shell en el contenedor de base de datos
# ==============================================================================

service ?= web
# Servicio por defecto para comandos que interactúan con contenedores específicos

# --- Project Configuration ---
DOCKER_COMPOSE_DEV = docker compose -p gtfseditor-backend-dev
DOCKER_COMPOSE_PROD = docker compose -p gtfseditor-backend-prod

# OS detection for path separators
ifeq ($(OS),Window_NT)
	COMPOSE_DEV = $(DOCKER_COMPOSE_DEV) -f docker\docker-compose.yml -f docker\docker-compose.dev.yml --profile dev
	COMPOSE_PROD = $(DOCKER_COMPOSE_PROD) -f docker\docker-compose.yml --profile prod
	COMPOSE_TEST = $(DOCKER_COMPOSE_DEV) -f docker\docker-compose.yml -f docker\docker-compose.dev.yml --profile test
	COMPOSE_CERT = $(DOCKER_COMPOSE_PROD) -f docker\docker-compose.yml -f docker\docker-compose.certbot.yml --profile certbot
else
	COMPOSE_DEV = $(DOCKER_COMPOSE_DEV) -f docker/docker-compose.yml -f docker/docker-compose.dev.yml --profile dev
	COMPOSE_PROD = $(DOCKER_COMPOSE_PROD) -f docker/docker-compose.yml --profile prod
	COMPOSE_TEST = $(DOCKER_COMPOSE_DEV) -f docker/docker-compose.yml -f docker/docker-compose.dev.yml --profile test
	COMPOSE_CERT = $(DOCKER_COMPOSE_PROD) -f docker/docker-compose.yml -f docker/docker-compose.certbot.yml --profile certbot
endif

MANAGE = python manage.py
PIP = pip install -r requirements.txt

.PHONY: help build rebuild up down db build_nginx migrate create_superuser container_bash db_shell prod_build prod_up prod_down prod_migrate prod_superuser container_bash_prod prod_db_shell emit_certificate test test_down install_local config_env

# --- Help ---
# Target para mostrar la ayuda de los comandos disponibles
help:
ifeq ($(OS),Window_NT)
	@echo ==============================================================================
	@echo Comandos de GTFS Editor Backend
	@echo ==============================================================================
	@echo Uso: make [comando] [service=nombre_servicio]
	@echo.
	@echo Desarrollo:
	@echo   build                Construye las imagenes de desarrollo
	@echo   rebuild              Reconstruye las imagenes (sin cache)
	@echo   up                   Levanta el entorno de desarrollo
	@echo   down                 Baja el entorno de desarrollo
	@echo   db                   Levanta solo la base de datos
	@echo   build_nginx          Reconstruye y reinicia Nginx
	@echo   migrate              Ejecuta migraciones localmente
	@echo   create_superuser     Crea un superusuario localmente
	@echo   container_bash       Bash en contenedor (default: service=web)
	@echo   db_shell             Consola psql en desarrollo
	@echo.
	@echo Produccion:
	@echo   prod_build           Construye imagenes de produccion
	@echo   prod_up              Levanta produccion (detached)
	@echo   prod_down            Baja produccion
	@echo   prod_migrate         Ejecuta migraciones en produccion
	@echo   prod_superuser       Crea superusuario en produccion
	@echo   container_bash_prod  Bash en contenedor de produccion
	@echo   prod_db_shell        Consola psql en produccion
	@echo   emit_certificate     Emite certificados con Certbot
	@echo.
	@echo Pruebas y Setup:
	@echo   test                 Ejecuta pruebas en contenedores
	@echo   test_down            Limpia contenedores de prueba
	@echo   install_local        Instala dependencias localmente
	@echo   config_env           Configura archivo .env inicial
	@echo ==============================================================================
else
	@echo "Uso: make [comando] [service=nombre_servicio]"
	@echo ""
	@echo "Comandos disponibles:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-20s\033[0m %s\n", $$1, $$2}'
endif

# --- Desarrollo (Development) ---
build: ## Construye las imágenes de desarrollo
	$(COMPOSE_DEV) build

rebuild: ## Reconstruye las imágenes de desarrollo sin usar cache
	$(COMPOSE_DEV) build --no-cache

up: ## Levanta el entorno de desarrollo
	$(COMPOSE_DEV) up

down: ## Baja el entorno de desarrollo
	$(COMPOSE_DEV) down

db: ## Levanta solo el servicio de base de datos en desarrollo
	$(COMPOSE_DEV) --profile dev up db

build_nginx: ## Reconstruye y reinicia el contenedor de Nginx en desarrollo
	$(COMPOSE_DEV) build nginx --no-cache
	$(COMPOSE_DEV) restart nginx

migrate: ## Ejecuta makemigrations y migrate localmente (requiere entorno local)
	$(MANAGE) makemigrations
	$(MANAGE) migrate

create_superuser: ## Crea un superusuario localmente (requiere entorno local)
	$(MANAGE) createsuperuser

container_bash: ## Abre una terminal bash en el contenedor especificado (por defecto service=web)
	$(COMPOSE_DEV) exec -it $(service) /bin/bash

db_shell: ## Abre la consola de PostgreSQL (psql) en el contenedor de desarrollo
	$(COMPOSE_DEV) exec -it db psql -U gtfseditor -d gtfseditor

# --- Producción (Production) ---
prod_build: ## Construye las imágenes de producción sin usar cache
	$(COMPOSE_PROD) build --no-cache

prod_up: ## Levanta el entorno de producción en segundo plano (detached)
	@$(COMPOSE_PROD) up -d

prod_down: ## Baja el entorno de producción
	$(COMPOSE_PROD) down

prod_migrate: ## Ejecuta las migraciones dentro del contenedor 'web' de producción
	$(COMPOSE_PROD) exec -it web python manage.py migrate

prod_superuser: ## Crea un superusuario dentro del contenedor 'web' de producción
	$(COMPOSE_PROD) exec -it web python manage.py createsuperuser

container_bash_prod: ## Abre una terminal bash en el contenedor de producción (por defecto service=web)
	$(COMPOSE_PROD) exec -it $(service) /bin/bash

prod_db_shell: ## Abre la consola de PostgreSQL (psql) en el contenedor de producción
	$(COMPOSE_PROD) exec -it db psql -U gtfseditor -d gtfseditor

emit_certificate: ## Intenta emitir/renovar certificados SSL con Certbot
	$(COMPOSE_CERT) up --abort-on-container-exit

# --- Pruebas (Testing) ---
test: ## Ejecuta la suite de pruebas en contenedores aislados
	$(COMPOSE_TEST) build
	$(COMPOSE_TEST) up --abort-on-container-exit

test_down: ## Limpia los contenedores de prueba
	$(COMPOSE_TEST) down

# --- Configuración Local (Local Setup) ---
install_local: ## Instala las dependencias de desarrollo localmente
	$(PIP) -r requirements-dev.txt

config_env: ## Configura el archivo .env inicial para desarrollo local
	@if [ ! -f .env ]; then \
		cp docker/docker_env .env; \
 	fi
	@sed -i 's/DB_HOST=db/DB_HOST=localhost/' .env
	@sed -i 's/DB_PORT=5432/DB_PORT=5431/' .env
	@sed -i 's/REDIS_HOST=cache/REDIS_HOST=localhost/' .env
	@sed -i 's/TESTING=False/TESTING=True/' .env
	@sed -i 's/DEBUG=False/DEBUG=True/' .env
	@sed -i 's/SERVER_MODE=.*/SERVER_MODE=test/' .env
