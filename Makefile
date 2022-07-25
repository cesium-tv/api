DOCKER = docker
VIDSRC_SRC = ${shell find vidsrc/vidsrc}
DOCKER_COMPOSE = docker-compose -p cesium.tv


api/vidsrc-*.tar.gz: $(VIDSRC_SRC)
	$(MAKE) -C vidsrc
	cp vidsrc/dist/vidsrc-*.tar.gz api/
	cd api && pipenv lock


.PHONY: build
build: api/vidsrc-*.tar.gz
	${DOCKER_COMPOSE} build


run:
	${DOCKER_COMPOSE} up


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
