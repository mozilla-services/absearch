SERVER_URL = https://search.stage.mozaws.net:443
VENV = .venv

# Hackety-hack around OSX system python bustage.
# The need for this should go away with a future osx/xcode update.
ARCHFLAGS = -Wno-error=unused-command-line-argument-hard-error-in-future
INSTALL = ARCHFLAGS=$(ARCHFLAGS) $(VENV)/bin/pip install
VIRTUALENV = virtualenv

.PHONY: install clean bench megabench

# Build virtualenv, to ensure we have all the dependencies.
.env.install:
	$(VIRTUALENV) $(VENV)
	$(INSTALL) pexpect >> loadtest.log && \
	$(INSTALL) configparser >> loadtest.log && \
	$(INSTALL) gevent >> loadtest.log && \
	$(INSTALL) git+git://github.com/mozilla-services/loads.git  >> loadtest.log && \
	$(INSTALL) git+git://github.com/mozilla-services/requests-hawk.git >> loadtest.log && \
	rm loadtest.log || cat loadtest.log
	touch $@

install: .env.install

# Clean all the things installed by `make build`.
clean:
	rm -rf $(VENV) *.pyc .env.install

# Run a single test from the venv machine, for sanity-checking.
test: install
	$(VENV)/bin/loads-runner --config=test.ini --server-url=$(SERVER_URL) loadtest.TestSearch.test_api

# Run a bench of 20 concurrent users.
bench:
	$(VENV)/bin/loads-runner --config=bench.ini --server-url=$(SERVER_URL) loadtest.TestSearch.test_api

# Run a much bigger bench, by submitting to broker in AWS.
megabench:
	$(VENV)/bin/loads-runner --config=megabench.ini --user-id=$(USER) --server-url=$(SERVER_URL) loadtest.TestSearch.test_api
