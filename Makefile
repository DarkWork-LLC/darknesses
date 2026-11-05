# DarknessMUD Django Makefile

.PHONY: clean deploy-init fresh help init lightclean lint migrate mud repair run setup test venv

VENV := .venv
PYTHON := $(VENV)/bin/python
MANAGE := $(PYTHON) manage.py
SETTINGS := darkness_django.settings.local

# PythonAnywhere uses 'venv' instead of '.venv'
PYTHONANYWHERE_VENV := venv
PYTHONANYWHERE_PYTHON := $(PYTHONANYWHERE_VENV)/bin/python
PYTHONANYWHERE_MANAGE := $(PYTHONANYWHERE_PYTHON) manage.py
PYTHONANYWHERE_SETTINGS := darkness_django.settings.production

help: ## Show this help message
	@echo "Usage: make [target]"
	@echo ""
	@echo "Targets:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2}'

venv: $(VENV)/bin/python ## Create virtual environment and install requirements
	$(PYTHON) -m pip install -r requirements/dev.txt

$(VENV)/bin/python:
	@echo "Creating virtual environment..."
	python3 -m venv $(VENV)
	$(PYTHON) -m pip install --upgrade pip

setup: venv ## Install dependencies

clean: ## Wipe .venv, cache, and world data while KEEPING human players
	@echo "Killing existing python processes..."
	-pkill -9 python || true
	@echo "Nuking virtual environment..."
	rm -rf $(VENV)
	@echo "Cleaning generated files..."
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -exec rm -f {} +
	rm -rf .pytest_cache .coverage htmlcov staticfiles
	@echo "Cleaning world data (bots, maps, NPCs, items) while preserving human players..."
	$(MANAGE) clean_world --confirm --settings=$(SETTINGS)
	@echo "Cleaning app migrations (optional, usually keeps them for DB consistency)..."
	# We keep migrations by default to ensure the DB can still be migrated. 
	# If you want to wipe migrations, use 'make repair'.

lightclean: ## Wipe .venv, cache, and world data but KEEP players (both human and bot)
	@echo "Killing existing python processes..."
	-pkill -9 python || true
	@echo "Nuking virtual environment..."
	rm -rf $(VENV)
	@echo "Cleaning generated files..."
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -exec rm -f {} +
	rm -rf .pytest_cache .coverage htmlcov staticfiles
	@echo "Cleaning world data (bots, maps, NPCs, items) while preserving ALL players..."
	$(MANAGE) clean_world --confirm --keep-players --settings=$(SETTINGS)
	@echo "Cleaning app migrations (optional, usually keeps them for DB consistency)..."
	# We keep migrations by default to ensure the DB can still be migrated. 
	# If you want to wipe migrations, use 'make repair'.

migrate: venv ## Run database migrations (local)
	$(MANAGE) makemigrations game --settings=$(SETTINGS)
	$(MANAGE) makemigrations --settings=$(SETTINGS)
	$(MANAGE) migrate --settings=$(SETTINGS)

init: migrate ## Initialize game world data (local) - WARNING: Wipes world state but keeps players
	$(MANAGE) init_game --settings=$(SETTINGS)

fresh: ## Wipe ALL user accounts and spawn a few fresh AI bots (world/rooms are kept)
	@echo "Deleting all user accounts and creating fresh bots..."
	$(MANAGE) migrate --settings=$(SETTINGS)
	$(MANAGE) create_bots --wipe-users --count 8 --settings=$(SETTINGS)

deploy-migrate: ## Run database migrations (PythonAnywhere/production)
	$(PYTHONANYWHERE_MANAGE) makemigrations game --settings=$(PYTHONANYWHERE_SETTINGS)
	$(PYTHONANYWHERE_MANAGE) makemigrations --settings=$(PYTHONANYWHERE_SETTINGS)
	$(PYTHONANYWHERE_MANAGE) migrate --settings=$(PYTHONANYWHERE_SETTINGS)

deploy-init: deploy-migrate ## Initialize game world data (PythonAnywhere/production)
	$(PYTHONANYWHERE_MANAGE) init_game --settings=$(PYTHONANYWHERE_SETTINGS)

run: venv ## Run the Django development server (kills existing ones first)
	@echo "Killing existing python processes..."
	-pkill -9 python || true
	$(MANAGE) migrate --settings=$(SETTINGS)
	$(MANAGE) runserver 0.0.0.0:8008 --settings=$(SETTINGS)

mud: venv ## Run the MUD Telnet server for MUD clients (kills existing ones first)
	@echo "Killing existing python processes..."
	-pkill -9 python || true
	$(MANAGE) migrate --settings=$(SETTINGS)
	$(MANAGE) start_mud_server --settings=$(SETTINGS)

deploy-run: ## Run the Django development server (PythonAnywhere/production)
	$(PYTHONANYWHERE_MANAGE) runserver 0.0.0.0:8008 --settings=$(PYTHONANYWHERE_SETTINGS)

repair: clean ## Deep repair: Nuke everything including the database and start over
	@echo "Wiping database and all migrations..."
	rm -f db.sqlite3
	find . -path "*/migrations/*.py" -not -name "__init__.py" -exec rm -f {} +
	$(MAKE) init

test: venv ## Run django tests
	$(MANAGE) test --settings=$(SETTINGS)

lint: venv ## Run static analysis
	@echo "Running lint (flake8)..."
	$(PYTHON) -m flake8 . --exclude=*/migrations/*,*/settings/*,$(VENV)/*