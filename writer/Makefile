# TESTS

build-tests:
	docker build -t openslides-datastore-writer-test -f Dockerfile.test .

run-integration-unit-tests: | build-tests
	docker run -t -v `pwd`/writer:/app/writer -v `pwd`/tests:/app/tests openslides-datastore-writer-test pytest tests/unit tests/integration

run-coverage-integration-unit: | build-tests
	docker run -t -v `pwd`/writer:/app/writer -v `pwd`/tests:/app/tests openslides-datastore-writer-test pytest tests/integration tests/unit --cov --cov-report html

run-integration-unit-tests-interactive: | build-tests
	docker run -ti -p 5000:5000 -v `pwd`/writer:/app/writer -v `pwd`/tests:/app/tests openslides-datastore-writer-test bash

run-cleanup: | build-tests
	docker run -ti -v `pwd`/writer:/app/writer -v `pwd`/tests:/app/tests openslides-datastore-writer-test ./cleanup.sh

# Docker compose
setup-docker-compose: | build-tests
	docker-compose -f dc.test.yml up -d
	docker-compose -f dc.test.yml exec writer wait-for-it --timeout=10 postgresql:5432
	docker-compose -f dc.test.yml exec writer wait-for-it --timeout=10 redis:6379

run-tests: | setup-docker-compose
	docker-compose -f dc.test.yml exec writer pytest
	docker-compose -f dc.test.yml down

run-tests-interactive: | setup-docker-compose
	docker-compose -f dc.test.yml exec writer bash
	docker-compose -f dc.test.yml down

run-system-tests: | setup-docker-compose
	docker-compose -f dc.test.yml exec writer pytest tests/system
	docker-compose -f dc.test.yml down

run-coverage: | setup-docker-compose
	docker-compose -f dc.test.yml exec writer pytest --cov --cov-report html
	docker-compose -f dc.test.yml down

# PROD

build-prod:
	docker build -t openslides-datastore-writer .

# DEVELOPMENT SERVER

build-dev:
	docker build -t openslides-datastore-writer-dev -f Dockerfile.dev .

run-dev: | build-dev
	docker run -t -v `pwd`/writer:/app/writer -p 127.0.0.1:8000:8000/tcp openslides-datastore-writer-dev
