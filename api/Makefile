DOCKER = docker
DOCKER_COMPOSE = docker compose -p cesium-tv
CWD = ${shell pwd}


.PHONY: test
test:
	${DOCKER_COMPOSE} run --rm api test


.PHONY: lint
lint:
	flake8 back/


.PHONY: migrations
migrations:
	${DOCKER_COMPOSE} run --user root -v ${CWD}:/app api python3 manage.py makemigrations rest
	sudo chown -R ${USER}:${USER} rest/migrations/


.PHONY: migrate
migrate:
	${DOCKER_COMPOSE} run api migrate


.PHONY: resetdb
resetdb:
	${DOCKER_COMPOSE} run api python3 manage.py reset_db --noinput


.PHONY: resetmigrations
resetmigrations:
	sudo rm -rf rest/migrations/__pycache__
	find rest/migrations/ -maxdepth 1 -type f ! -iname 0001_initial.py ! -name __init__.py -delete
	${MAKE} migrations


.PHONY: fixtures
fixtures:
	${DOCKER_COMPOSE} run api python3 manage.py loaddata --app rest site brand siteoption oauth2client channel package subscription
	${DOCKER_COMPOSE} run api python3 manage.py collectmedia --noinput


.PHONY: shell
shell:
	${DOCKER_COMPOSE} run api python3 manage.py shell_plus --print-sql


.PHONY: dbshell
dbshell:
	${DOCKER_COMPOSE} run api python3 manage.py dbshell


Pipfile.lock: Pipfile
	pipenv lock


lock: Pipfile.lock


.PHONY: build
build: lock


.PHONY: clean
clean:
