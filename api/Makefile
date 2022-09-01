DOCKER = docker
DOCKER_COMPOSE = docker-compose -p cesium.tv
CWD = ${shell pwd}


.PHONY: test
test:
	${DOCKER_COMPOSE} run --rm api test


.PHONY: lint
lint:
	flake8 back/


.PHONY: migrations
migrations:
	${DOCKER_COMPOSE} run -v ${CWD}:/app api python3 manage.py makemigrations rest
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
	${DOCKER_COMPOSE} run api python3 manage.py loaddata --app rest site platform publisher user brand siteoption oauth2client channel
	${DOCKER_COMPOSE} run api python3 manage.py collectmedia


.PHONY: shell
shell:
	${DOCKER_COMPOSE} run api python3 manage.py shell


.PHONY: clean
clean:
