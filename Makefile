PYTHON ?= python3
RUN_PYTHON := .venv/bin/python

.PHONY: setup setup-test setup-dev build site check test coverage verify verify-coverage a11y fetch live

# Production install: only what the build needs (used by Vercel).
setup:
	$(PYTHON) -c 'import sys; assert sys.version_info >= (3, 10), "Python 3.10+ required"'
	$(PYTHON) -m venv .venv
	$(RUN_PYTHON) -m pip install -q -r requirements.txt

# Adds coverage tooling without installing browsers or changing production setup.
setup-test: setup
	$(RUN_PYTHON) -m pip install -q -r requirements-test.txt

# Adds coverage and the browser accessibility tools used by `make a11y`.
setup-dev: setup
	$(RUN_PYTHON) -m pip install -q -r requirements-dev.txt

build: site

site:
	$(RUN_PYTHON) -m builder.build

# Re-reads every figure from its source file and checks every page.
check:
	$(RUN_PYTHON) -m builder.check

test:
	$(RUN_PYTHON) -m unittest discover -s tests -v

# Measure the full verification suite, then enforce .coveragerc's minimum.
# The first run replaces old data; append only this run's checks and unit tests.
coverage:
	$(RUN_PYTHON) -m coverage run -m builder.build
	$(RUN_PYTHON) -m coverage run --append -m builder.check
	$(RUN_PYTHON) -m coverage run --append -m unittest discover -s tests -v
	$(RUN_PYTHON) -m coverage report

verify: build check test

# CI uses the same checks with coverage, without running them twice.
verify-coverage: coverage

# axe-core accessibility checks at phone and desktop width.
a11y:
	$(RUN_PYTHON) -m builder.check --axe
	$(RUN_PYTHON) scripts/a11y_benchmark.py --strict > /dev/null

# Download the sources listed in sources/manifest.json (needs open network access).
fetch:
	$(RUN_PYTHON) scripts/fetch_sources.py

# Check the live site serves exactly this build (needs network access).
live: build
	$(RUN_PYTHON) scripts/check_live.py
