PYTHON ?= python3
RUN_PYTHON := .venv/bin/python

.PHONY: setup build site verify smoke a11y
setup:
	$(PYTHON) -c 'import sys; assert sys.version_info >= (3, 10), "Python 3.10+ required"'
	$(PYTHON) -m venv .venv
	$(RUN_PYTHON) -m pip install -r requirements.txt

build: site

site:
	$(RUN_PYTHON) scripts/build.py

verify:
	$(RUN_PYTHON) scripts/verify.py
	$(RUN_PYTHON) -m unittest discover -s tests -v

smoke: site
	$(RUN_PYTHON) -m unittest discover -s tests -k http -v
	$(RUN_PYTHON) scripts/a11y_check.py

a11y:
	$(RUN_PYTHON) scripts/a11y_check.py
