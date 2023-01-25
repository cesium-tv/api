DOCKER = docker
DOCKER_COMPOSE = docker-compose -p cesium.tv


.PHONY: build
build:
	${DOCKER_COMPOSE} build


.PHONY: run
run:
	${DOCKER_COMPOSE} up


.PHONY: stop
stop:
	${DOCKER_COMPOSE} stop


.PHONY: test
test:
	${MAKE} -C api test


.PHONY: lint
lint:
	${MAKE} -C api lint


.PHONY: rebuild
rebuild:
ifdef SERVICE
	${DOCKER_COMPOSE} stop ${SERVICE}
	${DOCKER_COMPOSE} rm -f ${SERVICE}
	${DOCKER_COMPOSE} build ${SERVICE}
	${DOCKER_COMPOSE} create ${SERVICE}
	${DOCKER_COMPOSE} start ${SERVICE}
else
	@echo "Please define SERVICE variable, ex:"
	@echo "make rebuild SERVICE=foo"
endif


.PHONY: clean
clean:
	${DOCKER_COMPOSE} rm --force
	$(MAKE) -C api clean


.PHONY: resetdb
resetdb:
	$(MAKE) -C api resetdb


.PHONY: resetmigrations
resetmigrations:
	$(MAKE) -C api resetmigrations


.PHONY: migrate
migrate:
	$(MAKE) -C api migrate


.PHONY: migrations
migrations:
	$(MAKE) -C api migrations


.PHONY: fixtures
fixtures:
	$(MAKE) -C api fixtures


.PHONY: image
image:
	${DOCKER} build . -f docker/Dockerfile
