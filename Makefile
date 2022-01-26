.PHONY: setup lint test
ENV='venv'

setup:
	@# It assumes the default python3 installation for Mac OS is pyhton 3.8
	@test -d $(ENV) || python3 -m venv $(ENV)
	@$(ENV)/bin/python3 -m pip install --upgrade pip
	@$(ENV)/bin/python3 -m pip install -r requirements-dev.txt
	@$(ENV)/bin/python3 -m pip install -r requirements.txt
	@# make the project packages discoverable (it uses the setup.py to install)
	@$(ENV)/bin/python3 -m pip install -e .

lint:
	@$(ENV)/bin/flake8

test:
	@$(ENV)/bin/python -m pytest -p no:cacheprovider tests/ --verbose --cov autoscaler --cov-fail=85

start:
	@$(ENV)/bin/python autoscaler start

clean:
	@rm -vrf venv/
	@rm -vrf .pytest_cache __pycache__/* ./build ./dist ./*.pyc ./*.egg-info