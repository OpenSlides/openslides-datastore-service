# TESTS

export COMPOSE_FILE=dc.test.yml

shared_test_coverage=89
reader_test_coverage=74
writer_test_coverage=98

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
	docker-compose exec $(MODULE) wait-for-it --timeout=10 postgresql:5432
ifdef USE_REDIS
	docker-compose exec $(MODULE) wait-for-it --timeout=10 redis:6379
endif

run-tests: | setup-docker-compose
	docker-compose exec $(MODULE) pytest
	docker-compose down

run-tests-interactive: | setup-docker-compose
	docker-compose exec $(MODULE) bash
	docker-compose down

run-system-tests: | setup-docker-compose
	docker-compose exec $(MODULE) pytest tests/system
	docker-compose down

run-coverage: | setup-docker-compose
	docker-compose exec $(MODULE) pytest --cov --cov-report html
	docker-compose down

run-travis: | setup-docker-compose
	scripts/travis.sh $(MODULE)

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
run-cleanup run-tests run-travis:
	$(MAKE) $@ MODULE=shared
	$(MAKE) $@ MODULE=reader
	$(MAKE) $@ MODULE=writer

# shared has no dev image
build-dev:
	$(MAKE) $@ MODULE=reader
	$(MAKE) $@ MODULE=writer
endif
