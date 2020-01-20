build-tests:
	docker build -t openslides-datastore-writer -f Dockerfile.test .

run-tests:
	docker run -t -v `pwd`/writer:/app/writer -v `pwd`/tests:/app/tests openslides-datastore-writer

run-tests-interactive:
	docker run -ti -v `pwd`/writer:/app/writer -v `pwd`/tests:/app/tests openslides-datastore-writer bash

run-mypy:
	docker run -t -v `pwd`/writer:/app/writer -v `pwd`/tests:/app/tests openslides-datastore-writer mypy tests writer
