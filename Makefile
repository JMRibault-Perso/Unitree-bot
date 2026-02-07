VENV ?= .venv
PY := $(VENV)/bin/python
PIP := $(VENV)/bin/pip

.PHONY: bootstrap venv deps submodules run-ui run-mock tests

venv:
	python3 -m venv $(VENV)
	$(PIP) install --upgrade pip
	$(PIP) install -r requirements.txt

deps:
	./scripts/pull_deps.sh

submodules:
	git submodule update --init --recursive

bootstrap: venv deps submodules

run-ui:
	$(PY) -m g1_app.ui.web_server

run-mock:
	$(PY) g1_app/test_mock_server.py

tests:
	cd g1_tests && $(PY) test_slam_topics_realtime.py
