# TESTS

ifdef MODULE
# targets are only available if MODULE is defined (meaning if called from a module=subdirectory)

args=-t -v `pwd`/shared/shared:/app/shared -v `pwd`/$(MODULE)/$(MODULE):/app/$(MODULE) -v `pwd`/$(MODULE)/tests:/app/tests -v `pwd`/cli:/app/cli

build-tests:
	docker build -t openslides-datastore-$(MODULE)-test -f Dockerfile.test . --build-arg MODULE=$(MODULE)

# Docker compose
setup-docker-compose: | build-tests
	docker-compose -f dc.test.yml up -d $(MODULE)
	docker-compose -f dc.test.yml exec $(MODULE) bash -c "chown -R $$(id -u $${USER}):$$(id -g $${USER}) /app"

run-tests-no-down: | setup-docker-compose
	docker-compose -f dc.test.yml exec $(MODULE) ./entrypoint.sh pytest

run-tests: | run-tests-no-down
	docker-compose -f dc.test.yml down

run-tests-interactive run-bash: | setup-docker-compose
	docker-compose -f dc.test.yml exec -u $$(id -u $${USER}):$$(id -g $${USER}) $(MODULE) ./entrypoint.sh bash
	docker-compose -f dc.test.yml down

run-system-tests: | setup-docker-compose
	docker-compose -f dc.test.yml exec $(MODULE) ./entrypoint.sh pytest tests/system
	docker-compose -f dc.test.yml down

run-coverage: | setup-docker-compose
	docker-compose -f dc.test.yml exec $(MODULE) ./entrypoint.sh pytest --cov --cov-report html
	docker-compose -f dc.test.yml down

run-ci-no-down: | setup-docker-compose
	docker-compose -f dc.test.yml exec $(MODULE) ./entrypoint.sh ./execute-ci.sh

run-ci: | run-ci-no-down
	docker-compose -f dc.test.yml down

run-cleanup: | setup-docker-compose
	docker-compose -f dc.test.yml exec -u $$(id -u $${USER}):$$(id -g $${USER}) $(MODULE) ./cleanup.sh
	docker-compose -f dc.test.yml down

run-cleanup-with-update: | setup-docker-compose
	docker-compose -f dc.test.yml exec -u $$(id -u $${USER}):$$(id -g $${USER}) $(MODULE) pip install -U -r requirements-testing.txt
	docker-compose -f dc.test.yml exec -u $$(id -u $${USER}):$$(id -g $${USER}) $(MODULE) ./cleanup.sh

# PROD
build_args=--build-arg MODULE=$(MODULE) --build-arg PORT=$(PORT)

build:
	docker build -t openslides-datastore-$(MODULE) $(build_args) .


# DEVELOPMENT SERVER
build-dev:
	docker build -t openslides-datastore-$(MODULE)-dev -f Dockerfile.dev $(build_args) .

run-dev: | build-dev
	docker-compose -f dc.dev.yml up -d $(MODULE)

run-dev-verbose: | build-dev
	docker-compose -f dc.dev.yml up $(MODULE)

endif


# the available targets without a MODULE:
ifndef MODULE


# shared has no dev or prod image
build build-dev:
	@$(MAKE) -C reader $@
	@$(MAKE) -C writer $@

run:
	docker-compose up -d
run-verbose:
	docker-compose up

# execute the target for all modules
run-cleanup run-cleanup-with-update:
	@$(MAKE) -C shared $@
	@$(MAKE) -C reader $@
	@$(MAKE) -C writer $@

# no-down mode speeds up the process by up to 50%
run-ci:
	@$(MAKE) -C shared run-ci-no-down
	@$(MAKE) -C reader run-ci-no-down
	@$(MAKE) -C writer run-ci

run-tests:
	@$(MAKE) -C shared run-tests-no-down
	@$(MAKE) -C reader run-tests-no-down
	@$(MAKE) -C writer run-tests
	@$(MAKE) run-dev
	@$(MAKE) run-full-system-tests

run-dev: | build-dev
	docker-compose -f dc.dev.yml up -d

run-dev-verbose: | build-dev
	docker-compose -f dc.dev.yml up

build-full-system-tests:
	docker build -t openslides-datastore-full-system-tests -f system_tests/Dockerfile .

fst_args=-ti -v `pwd`/system_tests/tests:/app/tests --network="host" --env-file=.env openslides-datastore-full-system-tests

run-full-system-tests: | build-full-system-tests
	docker run $(fst_args) pytest tests

run-full-system-tests-interactive: | build-full-system-tests
	docker run $(fst_args) bash

run-full-system-tests-cleanup: | build-full-system-tests
	docker run $(fst_args) ./cleanup.sh

run-full-system-tests-check: | build-full-system-tests
	docker run $(fst_args) ./execute-ci.sh

endif


# stopping is the same everywhere

stop:
	docker-compose down

stop-dev:
	docker-compose -f dc.dev.yml down
