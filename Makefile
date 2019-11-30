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


format: format-licenseheaders format-isort format-black
.PHONY: format

format-licenseheaders:
	@pipenv run licenseheaders --tmpl LICENSE.header --years 2019 --owner "Lukas Schmelzeisen" --dir nasty
	@pipenv run licenseheaders --tmpl LICENSE.header --years 2019 --owner "Lukas Schmelzeisen" --dir stubs --additional-extensions python=.pyi
	@pipenv run licenseheaders --tmpl LICENSE.header --years 2019 --owner "Lukas Schmelzeisen" --dir tests
.PHONY: format-licenseheaders

format-isort:
	@pipenv run isort --recursive .
.PHONY: format-isort

format-black:
	@pipenv run black .
.PHONY: format-black
