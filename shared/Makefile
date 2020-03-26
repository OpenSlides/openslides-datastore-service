export MODULE=shared

# just forward everthing to the main makefile so we don't have double code since everything is also needed in the reader
build-tests run-integration-unit-tests run-coverage-integration-unit run-integration-unit-tests-interactive run-cleanup setup-docker-compose run-tests-no-down run-tests run-tests-interactive run-system-tests run-coverage run-travis-no-down run-travis:
	@$(MAKE) -C .. $@ ||:
