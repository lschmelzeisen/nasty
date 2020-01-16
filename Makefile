venv:
	@python3.6 -m venv .venv
.PHONY: devvenv

devinstall:
	@pip install -e .[test,dev]
.PHONY: devinstall


test: test-pytest
.PHONY: test

test-pytest:
	@pytest --cov --cov-report= --cov-context test --html tests-report.html --self-contained-html
	@coverage html --dir tests-coverage
	@coverage report
.PHONY: test-pytest

test-tox:
	@coverage erase
	@tox
	@coverage html --dir tests-coverage
	@coverage report
.PHONY: test-tox


check: check-flake8 check-mypy check-vulture check-isort check-black
.PHONY: check

# Not using this rule because it even spams output in case of success (no quiet flag),
# and because most of the checking is already performed by flake8.
#check-autoflake:
#	@pipenv run autoflake --check --remove-all-unused-imports --remove-duplicate-keys --remove-unused-variables --recursive .
#.PHONY: check-autoflake

check-flake8:
	@flake8 nasty stubs tests setup.py vulture-whitelist.py
.PHONY: check-flake8

check-mypy:
	@mypy .
.PHONY: check-mypy

check-vulture:
	@vulture nasty vulture-whitelist.py
.PHONY: check-vulture

check-isort:
	@isort --check-only --recursive --quiet .
.PHONY: check-isort

check-black:
	@black --check .
.PHONY: check-black


format: format-licenseheaders format-autoflake format-isort format-black
.PHONY: format

format-licenseheaders:
	@licenseheaders --tmpl LICENSE.header --years 2019 --owner "Lukas Schmelzeisen" --dir nasty
	@licenseheaders --tmpl LICENSE.header --years 2019 --owner "Lukas Schmelzeisen" --dir stubs --additional-extensions python=.pyi
	@licenseheaders --tmpl LICENSE.header --years 2019 --owner "Lukas Schmelzeisen" --dir tests
.PHONY: format-licenseheaders

format-autoflake:
	@autoflake --in-place --remove-all-unused-imports --remove-duplicate-keys --remove-unused-variables --recursive .
.PHONY: format-autoflake

format-isort:
	@isort --recursive --quiet .
.PHONY: format-isort

format-black:
	@black .
.PHONY: format-black


publish: publish-setuppy publish-twine-check publish-twine-upload-testpypi
.PHONY: publish

publish-setuppy:
	@rm -rf build dist
	@python setup.py sdist bdist_wheel
.PHONY: publish-setuppy

publish-twine-check:
	@twine check dist/*
.PHONY: publish-twine-check

publish-twine-upload-testpypi:
	@twine upload --repository-url https://test.pypi.org/legacy/ dist/*
.PHONY: publish-twine-upload-testpypi

publish-twine-upload:
	@tine upload dist/*
.PHONY: publish-twine-upload


clean:
	@rm -rf .coverage* .eggs *.egg-info .mypy_cache .pytest_cache .tox .venv build dist nasty/version.py tests/util/.requests_cache.jsonl tests-coverage tests-report.html
.PHONY: clean


build-versionpy:
	@python setup.py --version
.PHONY:

build-vulture-whitelistpy:
	@vulture nasty --make-whitelist > vulture-whitelist.py || true
.PHONY: build-vulture-whitelistpy
