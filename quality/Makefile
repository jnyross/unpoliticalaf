# Run from the repository root: make -f quality/Makefile setup metrics
VENV ?= .venv
RUN_PYTHON := $(VENV)/bin/python

.PHONY: setup metrics tooling-tests
setup:
	$(MAKE) setup-test
	$(RUN_PYTHON) -m pip install -q -r quality/requirements.txt

tooling-tests:
	$(RUN_PYTHON) -m unittest discover -s quality/tests -v

# Same measured population and gate as make verify-coverage; each invocation
# retains its own reports, so a failure can never reuse an old success.
metrics: tooling-tests
	$(RUN_PYTHON) -m quality.measure
