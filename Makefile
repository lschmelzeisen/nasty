dev-environ:
	@PIPENV_VENV_IN_PROJECT=1 pipenv install --dev
.PHONY: dev-environ


test: test-pytest
.PHONY: test

test-pytest:
	@pipenv run pytest tests
.PHONY: test-pytest


check: check-flake8 check-mypy check-isort check-black
.PHONY: check

check-flake8:
	@pipenv run flake8
.PHONY: check-flake8

check-mypy:
	@pipenv run mypy .
.PHONY: check-mypy

check-isort:
	@pipenv run isort --check-only --recursive .
.PHONY: check-isort

check-black:
	@pipenv run black --check .
.PHONY: check-black


format: format-isort format-black
.PHONY: format

format-isort:
	@pipenv run isort --recursive .
.PHONY: format-isort

format-black:
	@pipenv run black .
.PHONY: format-black
