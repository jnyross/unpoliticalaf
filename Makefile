PYTHON ?= python3

.PHONY: setup build site verify smoke
setup:
	$(PYTHON) -c 'import sys; assert sys.version_info >= (3, 10), "Python 3.10+ required"; print("Setup OK: Python standard library only; no packages to install")'

build: site

site:
	$(PYTHON) scripts/build.py

verify:
	$(PYTHON) -m unittest discover -s tests -v

smoke: site
	$(PYTHON) -m unittest discover -s tests -k http -v
