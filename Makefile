SERVICE=datastore

# Build images for different contexts

build-dev:
	bash ../dev/scripts/makefile/build-service.sh $(SERVICE) dev reader 9010
	bash ../dev/scripts/makefile/build-service.sh $(SERVICE) dev writer 9011

build-prod:
	bash ../dev/scripts/makefile/build-service.sh $(SERVICE) prod reader 9010
	bash ../dev/scripts/makefile/build-service.sh $(SERVICE) prod writer 9011

build-test:
	bash ../dev/scripts/makefile/build-service.sh $(SERVICE) tests

# TESTS

ifdef MODULE
# targets are only available if MODULE is defined (meaning if called from a module=subdirectory)

# PROD
build_args=--build-arg MODULE=$(MODULE) --build-arg PORT=$(PORT)

build:
	docker build -t openslides-datastore-$(MODULE) $(build_args) .

run-dev-standalone: | build-dev
	docker compose -f dc.dev.yml up -d $(MODULE)

run-dev-verbose: | build-dev
	docker compose -f dc.dev.yml up $(MODULE)

endif


# the available targets without a MODULE:
ifndef MODULE
## TESTS

build-tests:
	make build-test

build-tests-old:
	make build-test

rebuild-tests:
	docker build . --tag=openslides-datastore-tests --no-cache --build-arg CONTEXT=tests

setup-docker-compose: | build-tests-old
	docker compose -f dc.test.yml up -d
	docker compose -f dc.test.yml exec -T datastore bash -c "chown -R $$(id -u $${USER}):$$(id -g $${USER}) /app"

run-tests-no-down: | setup-docker-compose
	docker compose -f dc.test.yml exec datastore ./entrypoint.sh pytest

run-test:| run-tests-no-down
	docker compose -f dc.test.yml down
	@$(MAKE) run-dev
	@$(MAKE) run-full-system-tests

run-tests: 
	bash dev/run-tests.sh

run-dev run-bash: | setup-docker-compose
	docker compose -f dc.test.yml exec -u $$(id -u $${USER}):$$(id -g $${USER}) datastore ./entrypoint.sh bash

run-coverage: | setup-docker-compose
	docker compose -f dc.test.yml exec datastore ./entrypoint.sh pytest --cov --cov-report html
	docker compose -f dc.test.yml down

run-ci-no-down: | setup-docker-compose
	docker compose -f dc.test.yml exec -T datastore ./entrypoint.sh ./execute-ci.sh

run-ci: 
	bash dev/run-ci.sh 

run-cleanup: | setup-docker-compose
	docker compose -f dc.test.yml exec -u $$(id -u $${USER}):$$(id -g $${USER}) datastore ./cleanup.sh
	docker compose -f dc.test.yml down

run-cleanup-with-update: | setup-docker-compose
	docker compose -f dc.test.yml exec -u $$(id -u $${USER}):$$(id -g $${USER}) datastore pip install -U -r requirements-testing.txt
	docker compose -f dc.test.yml exec -u $$(id -u $${USER}):$$(id -g $${USER}) datastore ./cleanup.sh

stop-tests:
	docker compose -f dc.test.yml down

fst_args=-v `pwd`/system_tests/system_tests:/app/system_tests --network="host" --env-file=.env  -u $$(id -u $${USER}):$$(id -g $${USER}) openslides-datastore-full-system-tests

build-full-system-tests:
	docker build -t openslides-datastore-full-system-tests -f system_tests/Dockerfile --build-arg CHOWN=$$(id -u $${USER}):$$(id -g $${USER}) .

run-full-system-tests: | build-full-system-tests
	docker run -ti $(fst_args) pytest system_tests

run-full-system-tests-interactive: | build-full-system-tests
	docker run -ti $(fst_args) bash

run-full-system-tests-cleanup: | build-full-system-tests
	docker run -ti $(fst_args) ./cleanup.sh

run-full-system-tests-check: | build-full-system-tests
	docker run $(fst_args) ./execute-ci.sh system_tests


# shared has no dev or prod image
# This runs the target 'build' or 'build-dev' on the Makefile in the reader and writer subdirectory
#build build-dev:
#	@$(MAKE) -C reader $@
#	@$(MAKE) -C writer $@
run:
	docker compose up -d

run-verbose:
	docker compose up

run-dev-standalone: | build-dev
	docker compose -f dc.dev.yml up -d

run-dev-verbose: | build-dev
	docker compose -f dc.dev.yml up

ci-run-system-tests:
	docker compose -f dc.dev.yml up -d
	make run-full-system-tests-check
	make stop-dev

endif

# stopping is the same everywhere
stop:
	docker compose down --remove-orphans

stop-dev:
	docker compose -f dc.dev.yml down --remove-orphans
