PYTHON ?= python3
RUN_PYTHON := .venv/bin/python
PYTHON_SOURCES := builder scripts tests quality

.PHONY: setup setup-test setup-dev setup-typing build site benchmark check test test-stability coverage verify-coverage verify a11y fetch live lint format format-check typecheck check-deps quality

# Production install: only what the build needs (used by Vercel).
setup:
	$(PYTHON) -c 'import sys; assert sys.version_info >= (3, 10), "Python 3.10+ required"'
	$(PYTHON) -m venv .venv
	$(RUN_PYTHON) -m pip install -q -r requirements.txt

# Unit-test tools, without the optional browser accessibility dependencies.
setup-test: setup
	$(RUN_PYTHON) -m pip install -q -r requirements-test.txt

# Adds test, browser, typing, lint, formatting and dashboard tools.
setup-dev: setup
	$(RUN_PYTHON) -m pip install -q -r requirements-dev.txt

setup-typing: setup
	$(RUN_PYTHON) -m pip install -q -r requirements-typing.txt

build: site

site:
	$(RUN_PYTHON) -m builder.build

# Real fresh-process build; measurements never enter deterministic site output.
benchmark:
	$(RUN_PYTHON) scripts/build_performance.py

# Re-reads every figure from its source file and checks every page.
check:
	$(RUN_PYTHON) -m builder.check

test:
	PYTEST_ADDOPTS= $(RUN_PYTHON) -m scripts.test_stability --runs 1 --output test-results/performance

# Same canonical pytest population, with three fresh processes and no forgiven failures.
test-stability: build
	PYTEST_ADDOPTS= $(RUN_PYTHON) -m scripts.test_stability

lint:
	$(RUN_PYTHON) -m ruff check --config ruff.toml $(PYTHON_SOURCES)

# One recursive first-party selection; never format retained data or output.
# Explicit configuration prevents nested tool configs from changing the policy.
format:
	$(RUN_PYTHON) -m black --config pyproject.toml $(PYTHON_SOURCES)

format-check:
	$(RUN_PYTHON) -m black --config pyproject.toml --check --diff $(PYTHON_SOURCES)

typecheck:
	$(RUN_PYTHON) -m compileall -q -f $(PYTHON_SOURCES)
	$(RUN_PYTHON) -m mypy --config-file mypy.ini

check-deps:
	$(RUN_PYTHON) -m deptry .
	cd quality && ../$(RUN_PYTHON) -m deptry .

# Extend this aggregate as further tooling lands; never replace existing gates.
quality: lint format-check typecheck check-deps test-stability
	$(RUN_PYTHON) scripts/check_agents.py
	$(MAKE) -f quality/Makefile metrics

verify: build check test

# Combined build/check/canonical pytest measurement, including nested reporters.
coverage:
	$(RUN_PYTHON) -m quality.measure

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
