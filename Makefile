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

# Not using this rule because it even spams output in case of success (no quiet flag),
# and because most of the checking is already performed by flake8.
#check-autoflake:
#	@pipenv run autoflake --check --remove-all-unused-imports --remove-duplicate-keys --remove-unused-variables --recursive .
#.PHONY: check-autoflake

check-flake8:
	@pipenv run flake8
.PHONY: check-flake8

check-mypy:
	@pipenv run mypy .
.PHONY: check-mypy

check-isort:
	@pipenv run isort --check-only --recursive --quiet .
.PHONY: check-isort

check-black:
	@pipenv run black --check .
.PHONY: check-black


format: format-licenseheaders format-autoflake format-isort format-black
.PHONY: format

format-licenseheaders:
	@pipenv run licenseheaders --tmpl LICENSE.header --years 2019 --owner "Lukas Schmelzeisen" --dir nasty
	@pipenv run licenseheaders --tmpl LICENSE.header --years 2019 --owner "Lukas Schmelzeisen" --dir stubs --additional-extensions python=.pyi
	@pipenv run licenseheaders --tmpl LICENSE.header --years 2019 --owner "Lukas Schmelzeisen" --dir tests
.PHONY: format-licenseheaders

format-autoflake:
	@pipenv run autoflake --in-place --remove-all-unused-imports --remove-duplicate-keys --remove-unused-variables --recursive .
.PHONY: format-autoflake

format-isort:
	@pipenv run isort --recursive --quiet .
.PHONY: format-isort

format-black:
	@pipenv run black .
.PHONY: format-black
