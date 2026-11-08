PYTHON ?= python3
VENV ?= .venv
RUN_PYTHON := $(VENV)/bin/python
PYTHON_SOURCES := builder scripts tests quality

.PHONY: setup setup-test setup-dev-tools setup-dev hooks setup-typing setup-quality setup-architecture architecture complexity duplication tracing build site benchmark check test test-stability coverage verify-coverage verify a11y fetch live lint format format-check typecheck check-deps quality

# Production install: only what the build needs (used by Vercel).
setup:
	$(PYTHON) -c 'import sys; assert sys.version_info >= (3, 10), "Python 3.10+ required"'
	$(PYTHON) -m venv $(VENV)
	$(RUN_PYTHON) -m pip install -q -r requirements.txt

# Unit-test tools, without the optional browser accessibility dependencies.
setup-test: setup
	$(RUN_PYTHON) -m pip install -q -r requirements-test.txt

# Containers share source with the outer checkout, never its installed hooks.
setup-dev-tools: setup
	$(RUN_PYTHON) -m pip install -q -r requirements-dev.txt

# Adds developer tools and the hook in Git checkouts, not Git-free CI exports.
setup-dev: setup-dev-tools
	@if test -e .git; then $(MAKE) hooks; else echo "No Git metadata; hook installation skipped."; fi

# Explicitly reinstall after recreating the venv. Never call on the agent host.
hooks:
	$(RUN_PYTHON) -m pre_commit install

setup-typing: setup
	$(RUN_PYTHON) -m pip install -q -r requirements-typing.txt

# Browser-free setup, including the same pytest pin used by every regression.
setup-architecture: setup-test

# Real analyzer errors and broken contracts stop before the regression suite.
architecture:
	$(VENV)/bin/lint-imports --config .importlinter --no-cache
	PYTEST_ADDOPTS= $(RUN_PYTHON) -m pytest tests/architecture

# Reuse the dashboard's canonical pinned Radon requirements.
setup-quality:
	$(PYTHON) -m venv $(VENV)
	$(RUN_PYTHON) -m pip install -q -r quality/requirements.txt

complexity:
	$(RUN_PYTHON) -m unittest discover -s tests/quality -v
	$(RUN_PYTHON) scripts/check_complexity.py

# Install the locked Node 22 developer tools with npm ci --ignore-scripts first.
duplication:
	npm run check:duplicates

tracing:
	npm test

build: site

site:
	$(RUN_PYTHON) -m builder.build

.PHONY: production-build production-verify
production-build:
	$(RUN_PYTHON) -m builder.build --production

production-verify: production-build check test

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
	cd quality && $(abspath $(RUN_PYTHON)) -m deptry .

# Extend this aggregate as further tooling lands; never replace existing gates.
quality: lint format-check typecheck check-deps complexity duplication tracing architecture test-stability
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
live: production-build
	$(RUN_PYTHON) scripts/check_live.py
