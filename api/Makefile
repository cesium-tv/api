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
	rm -f rest/migrations/00*.py
	${MAKE} migrations


.PHONY: shell
shell:
	${DOCKER_COMPOSE} run api python3 manage.py shell
