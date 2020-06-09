# TESTS

ifdef MODULE
# targets are only available if MODULE is defined (meaning if called from a module=subdirectory)

args=-t -v `pwd`/shared/shared:/app/shared -v `pwd`/$(MODULE)/$(MODULE):/app/$(MODULE) -v `pwd`/$(MODULE)/tests:/app/tests -v `pwd`/cli:/app/cli

build-tests:
	docker build -t openslides-datastore-$(MODULE)-test -f Dockerfile.test . --build-arg MODULE=$(MODULE)

run-integration-unit-tests: | build-tests
	docker run $(args) openslides-datastore-$(MODULE)-test pytest tests/unit tests/integration

run-coverage-integration-unit: | build-tests
	docker run $(args) openslides-datastore-$(MODULE)-test pytest tests/integration tests/unit --cov --cov-report html

run-integration-unit-tests-interactive: | build-tests
	docker run -i -p 5000:5000 $(args) openslides-datastore-$(MODULE)-test bash

run-cleanup: | build-tests
	docker run -i $(args) openslides-datastore-$(MODULE)-test ./cleanup.sh

# Docker compose
setup-docker-compose: | build-tests
	docker-compose -f dc.test.yml up -d $(MODULE)

run-tests-no-down: | setup-docker-compose
	docker-compose -f dc.test.yml exec $(MODULE) ./entrypoint.sh pytest

run-tests: | run-tests-no-down
	docker-compose -f dc.test.yml down

run-tests-interactive run-bash: | setup-docker-compose
	docker-compose -f dc.test.yml exec $(MODULE) ./entrypoint.sh bash
	docker-compose -f dc.test.yml down

run-system-tests: | setup-docker-compose
	docker-compose -f dc.test.yml exec $(MODULE) ./entrypoint.sh pytest tests/system
	docker-compose -f dc.test.yml down

run-coverage: | setup-docker-compose
	docker-compose -f dc.test.yml exec $(MODULE) ./entrypoint.sh pytest --cov --cov-report html
	docker-compose -f dc.test.yml down

run-travis-no-down: | setup-docker-compose
	docker-compose -f dc.test.yml exec $(MODULE) ./entrypoint.sh ./execute-travis.sh

run-travis: | run-travis-no-down
	docker-compose -f dc.test.yml down

# PROD

# pass env variables to container
build_args=--build-arg MODULE=$(MODULE) --build-arg PORT=$(PORT)

build:
	docker build -t openslides-datastore-$(MODULE) .  $(build_args)

run:
	docker-compose up -d $(MODULE)

run-verbose:
	docker-compose up $(MODULE)


build-prod:
	docker build -t openslides-datastore-$(MODULE) -f Dockerfile.prod .  $(build_args)

run-prod: | build-prod
	docker-compose -f dc.prod.yml up -d $(MODULE)

run-prod-verbose: | build-prod
	docker-compose -f dc.prod.yml up $(MODULE)


# DEVELOPMENT SERVER

build-dev:
	docker build -t openslides-datastore-$(MODULE)-dev -f Dockerfile.dev . $(build_args)

run-dev: | build-dev
	docker-compose -f dc.dev.yml up -d $(MODULE)

run-dev-verbose: | build-dev
	docker-compose -f dc.dev.yml up $(MODULE)


# postgres and redis (if needed) must be running for this
run-dev-manually: | build-dev
	docker run -t \
			   -v `pwd`/shared/shared:/app/shared \
			   -v `pwd`/$(MODULE)/$(MODULE):/app/$(MODULE) \
			   -p 127.0.0.1:$(PORT):$(PORT)/tcp \
			   openslides-datastore-$(MODULE)-dev

endif


# the available targets without a MODULE:

ifndef MODULE


# shared has no dev or prod image
run build build-dev run-dev run-dev-manually build-prod run-prod:
	@$(MAKE) -C reader $@
	@$(MAKE) -C writer $@

# execute the target for all modules
run-cleanup:
	@$(MAKE) -C shared $@
	@$(MAKE) -C reader $@
	@$(MAKE) -C writer $@

# no-down mode speeds up the process by up to 50%
run-tests run-travis:
	@$(MAKE) -C shared $@-no-down
	@$(MAKE) -C reader $@-no-down
	@$(MAKE) -C writer $@

run-verbose:
	docker-compose up

run-prod-verbose: | build-prod
	docker-compose -f dc.prod.yml up

run-dev-verbose:
	docker-compose -f dc.dev.yml up


endif


# stopping is the same everywhere

stop:
	docker-compose down

stop-prod:
	docker-compose -f dc.prod.yml down

stop-dev:
	docker-compose -f dc.dev.yml down
