PYTHON ?= python3
RUN_PYTHON := .venv/bin/python

.PHONY: setup setup-test setup-dev setup-typing build site check test verify a11y fetch live lint typecheck check-deps quality

# Production install: only what the build needs (used by Vercel).
setup:
	$(PYTHON) -c 'import sys; assert sys.version_info >= (3, 10), "Python 3.10+ required"'
	$(PYTHON) -m venv .venv
	$(RUN_PYTHON) -m pip install -q -r requirements.txt

# Unit-test tools, without the optional browser accessibility dependencies.
setup-test: setup
	$(RUN_PYTHON) -m pip install -q -r requirements-test.txt

# Adds test, browser, typing, lint and dashboard tools.
setup-dev: setup
	$(RUN_PYTHON) -m pip install -q -r requirements-dev.txt

setup-typing: setup
	$(RUN_PYTHON) -m pip install -q -r requirements-typing.txt

build: site

site:
	$(RUN_PYTHON) -m builder.build

# Re-reads every figure from its source file and checks every page.
check:
	$(RUN_PYTHON) -m builder.check

test:
	$(RUN_PYTHON) -m pytest tests quality/tests

lint:
	$(RUN_PYTHON) -m ruff check builder scripts tests quality

typecheck:
	$(RUN_PYTHON) -m compileall -q -f builder scripts tests quality
	$(RUN_PYTHON) -m mypy --config-file mypy.ini

check-deps:
	$(RUN_PYTHON) -m deptry .
	cd quality && ../$(RUN_PYTHON) -m deptry .

# Extend this aggregate as further tooling lands; never replace existing gates.
quality: lint typecheck check-deps
	$(RUN_PYTHON) scripts/check_agents.py
	$(MAKE) -f quality/Makefile metrics

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
