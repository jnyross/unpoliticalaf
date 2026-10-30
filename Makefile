PYTHON ?= python3

.PHONY: setup build site verify smoke a11y
setup:
	$(PYTHON) -c 'import sys; assert sys.version_info >= (3, 10), "Python 3.10+ required"'
	$(PYTHON) -m pip install -r requirements.txt

build: site

site:
	$(PYTHON) scripts/build.py

verify:
	$(PYTHON) scripts/verify.py
	$(PYTHON) -m unittest discover -s tests -v

smoke: site
	$(PYTHON) -m unittest discover -s tests -k http -v
	$(PYTHON) scripts/a11y_check.py

a11y:
	$(PYTHON) scripts/a11y_check.py
