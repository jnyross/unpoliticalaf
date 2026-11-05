# Run from the repository root: make -f quality/Makefile setup metrics
PYTHON := .venv/bin/python
COVERAGE := $(PYTHON) -m coverage
export COVERAGE_RCFILE := quality/coverage.ini

.PHONY: setup metrics tooling-tests
setup:
	$(MAKE) setup
	$(PYTHON) -m pip install -q -r quality/requirements.txt

tooling-tests:
	$(PYTHON) -m unittest discover -s quality/tests -v

# Measure the unchanged build + independent check + unit-test verification path.
# coverage run starts fresh; --append combines the three real execution phases.
metrics: tooling-tests
	mkdir -p quality-reports
	$(COVERAGE) run -m builder.build
	$(COVERAGE) run --append -m builder.check
	$(COVERAGE) run --append -m unittest discover -s tests -v
	$(COVERAGE) report
	$(COVERAGE) html
	$(COVERAGE) xml
	$(COVERAGE) json
	$(PYTHON) quality/report.py
