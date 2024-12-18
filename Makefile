ENV='venv'
export DEST_TEMPLATE_PATH=/tmp/


.PHONY: publish
publish:
	@head=$(shell git rev-parse --short=7 HEAD) && \
	docker build -t <CHANGE_ME>.io/bitbucket-runner-autoscaler:v0.1.4-$${head} . && \
	docker push <CHANGE_ME>/bitbucket-runner-autoscaler:v0.1.4-$${head}

.PHONY: all
all: setup lint test

.PHONY: setup
setup:
	@# It assumes the default python3 installation for Mac OS is python 3.8
	@test -d $(ENV) || python3 -m venv $(ENV)
	@$(ENV)/bin/python3 -m pip install --upgrade pip
	@$(ENV)/bin/python3 -m pip install -r requirements-dev.txt
	@$(ENV)/bin/python3 -m pip install -r requirements.txt
	@# make the project packages discoverable (it uses the setup.py to install)
	@$(ENV)/bin/python3 -m pip install -e .

.PHONY: lint
lint:
	@$(ENV)/bin/flake8

.PHONY: test
test:
	@$(ENV)/bin/python -m pytest -p no:cacheprovider tests/ --verbose --cov autoscaler --cov-fail-under=90

.PHONY: clean
clean:
	@rm -vrf venv/
	@rm -vrf .pytest_cache __pycache__/* ./build ./dist ./*.pyc ./*.egg-info
