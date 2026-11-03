PY ?= 3.12
COMPILE = uv pip compile --universal --python-version $(PY) --generate-hashes -q \
          --custom-compile-command "make lock"

.PHONY: lock upgrade install test audit tree drift tamper unpinned

lock:          ## regenerate locks from *.in without upgrading existing pins
	$(COMPILE) requirements.in -o requirements.txt
	$(COMPILE) requirements-dev.in -o requirements-dev.txt

upgrade:       ## deliberately move every pin (incl. transitive) to latest allowed
	$(COMPILE) --upgrade requirements.in -o requirements.txt
	$(COMPILE) --upgrade requirements-dev.in -o requirements-dev.txt

install:       ## hash-verified install from the lock
	python -m pip install --require-hashes --no-deps -r requirements.txt -r requirements-dev.txt

test:
	pytest -q

audit:
	pip-audit --strict --disable-pip -r requirements.txt -r requirements-dev.txt

tree:
	pipdeptree -p boto3,moto

drift:         ## how the unpinned file resolves now vs mid-2024
	python scripts/show_drift.py 2024-06-01

tamper:        ## show --require-hashes blocking a swapped artifact
	bash scripts/tamper_demo.sh

unpinned:      ## install the unpinned file into ./.venv-unpinned and count packages
	python -m venv .venv-unpinned && .venv-unpinned/bin/pip install -q -r unpinned/requirements.txt
	@echo "You wrote $$(grep -cv '^\s*$$' unpinned/requirements.txt) lines; pip installed $$(.venv-unpinned/bin/pip freeze | wc -l) packages:"
	@.venv-unpinned/bin/pip freeze
