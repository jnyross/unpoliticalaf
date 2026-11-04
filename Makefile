PYTHON ?= python3
RUN_PYTHON := .venv/bin/python

.PHONY: setup setup-dev build site check test verify a11y fetch live

# Production install: only what the build needs (used by Vercel).
setup:
	$(PYTHON) -c 'import sys; assert sys.version_info >= (3, 10), "Python 3.10+ required"'
	$(PYTHON) -m venv .venv
	$(RUN_PYTHON) -m pip install -q -r requirements.txt

# Adds the browser accessibility tools used by `make a11y`.
setup-dev: setup
	$(RUN_PYTHON) -m pip install -q -r requirements-dev.txt

build: site

site:
	$(RUN_PYTHON) -m builder.build

# Re-reads every figure from its source file and checks every page.
check:
	$(RUN_PYTHON) -m builder.check

test:
	$(RUN_PYTHON) -m scripts.test_performance

verify: build check test

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
