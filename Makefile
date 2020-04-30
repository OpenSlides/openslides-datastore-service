# TESTS

export COMPOSE_FILE=dc.test.yml

ifdef MODULE
# targets are only available if MODULE is defined (meaning if called from a module=subdirectory)

build-tests:
	docker build -t openslides-datastore-$(MODULE)-test -f $(MODULE)/Dockerfile.test .

run-integration-unit-tests: | build-tests
	docker run -t -v `pwd`/shared/shared:/app/shared -v `pwd`/$(MODULE)/$(MODULE):/app/$(MODULE) -v `pwd`/$(MODULE)/tests:/app/tests openslides-datastore-$(MODULE)-test pytest tests/unit tests/integration

run-coverage-integration-unit: | build-tests
	docker run -t -v `pwd`/shared/shared:/app/shared -v `pwd`/$(MODULE)/$(MODULE):/app/$(MODULE) -v `pwd`/$(MODULE)/tests:/app/tests openslides-datastore-$(MODULE)-test pytest tests/integration tests/unit --cov --cov-report html

run-integration-unit-tests-interactive: | build-tests
	docker run -ti -p 5000:5000 -v `pwd`/shared/shared:/app/shared -v `pwd`/$(MODULE)/$(MODULE):/app/$(MODULE) -v `pwd`/$(MODULE)/tests:/app/tests openslides-datastore-$(MODULE)-test bash

run-cleanup: | build-tests
	docker run -ti -v `pwd`/shared/shared:/app/shared -v `pwd`/$(MODULE)/$(MODULE):/app/$(MODULE) -v `pwd`/$(MODULE)/tests:/app/tests openslides-datastore-$(MODULE)-test ./cleanup.sh

# Docker compose
setup-docker-compose: | build-tests
	docker-compose up -d $(MODULE)
	docker-compose exec $(MODULE) wait-for-it --timeout=15 postgresql:5432
ifdef USE_REDIS
	docker-compose exec $(MODULE) wait-for-it --timeout=15 redis:6379
endif

run-tests-no-down: | setup-docker-compose
	docker-compose exec $(MODULE) pytest

run-tests: | run-tests-no-down
	docker-compose down

run-tests-interactive run-bash: | setup-docker-compose
	docker-compose exec $(MODULE) bash
	docker-compose down

run-system-tests: | setup-docker-compose
	docker-compose exec $(MODULE) pytest tests/system
	docker-compose down

run-coverage: | setup-docker-compose
	docker-compose exec $(MODULE) pytest --cov --cov-report html
	docker-compose down

run-travis-no-down: | setup-docker-compose
	docker-compose exec $(MODULE) ./execute-travis.sh $(MODULE)

run-travis: | run-travis-no-down
	docker-compose down

# PROD

build-prod:
	docker build -t openslides-datastore-$(MODULE) -f $(MODULE)/Dockerfile .

# DEVELOPMENT SERVER

build-dev:
	docker build -t openslides-datastore-$(MODULE)-dev -f $(MODULE)/Dockerfile.dev .

run-dev: | build-dev
	docker run -t -v `pwd`/shared/shared:/app/shared -v `pwd`/$(MODULE)/$(MODULE):/app/$(MODULE) -p 127.0.0.1:8000:8000/tcp openslides-datastore-$(MODULE)-dev

endif


# the two available targets without a MODULE:

ifndef MODULE

# execute the target for all modules
run-cleanup:
	@$(MAKE) -C shared $@
	@$(MAKE) -C reader $@
	@$(MAKE) -C writer $@

# no-down mode speeds up the process by up to 50%
run-tests run-travis:
	@$(MAKE) -C shared $@-no-down
	@$(MAKE) -C reader $@-no-down
	@$(MAKE) -C writer $@-no-down
	docker-compose down

# shared has no dev image
build-dev:
	@$(MAKE) -C reader $@
	@$(MAKE) -C writer $@

run-prod:
	docker-compose -f dc.prod.yml up -d

endif
