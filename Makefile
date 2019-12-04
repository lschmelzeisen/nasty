dev-environ:
	@PIPENV_VENV_IN_PROJECT=1 pipenv install --dev
.PHONY: dev-environ


test: test-pytest
.PHONY: test

test-pytest:
	@pipenv run pytest tests
.PHONY: test-pytest


check: check-flake8 check-mypy check-vulture check-isort check-black
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

check-vulture:
	@pipenv run vulture nasty vulture-whitelist.py
.PHONY: check-vulture

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
	@find stubs/ -name "*.pyi" -exec rename ".pyi" ".py" {} \;
	@pipenv run licenseheaders --tmpl LICENSE.header --years 2019 --owner "Lukas Schmelzeisen" --dir stubs
	@find stubs/ -name "*.py" -exec rename ".py" ".pyi" {} \;
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


publish: publish-pipenv-setup publish-setuppy publish-twine-check publish-twine-upload-testpypi
.PHONY: publish

publish-pipenv-setup:
	@pipenv run pipenv-setup sync --dev --pipfile
.PHONY: publish-pipenv-setuppy

publish-setuppy:
	@rm -rf build dist
	@pipenv run python setup.py sdist bdist_wheel
.PHONY: publish-setuppy

publish-twine-check:
	@pipenv run twine check dist/*
.PHONY: publish-twine-check

publish-twine-upload-testpypi:
	@pipenv run twine upload --repository-url https://test.pypi.org/legacy/ dist/*
.PHONY: publish-twine-upload-testpypi


clean:
	@rm -rf .eggs .mypy_cache .pytest_cache build dist nasty/version.py tests/util/.requests_cache.pickle
	@pipenv --rm
.PHONY: clean


build-versionpy:
	@pipenv run python setup.py --version
.PHONY:

build-vulture-whitelistpy:
	@pipenv run vulture nasty --make-whitelist > vulture-whitelist.py || true
.PHONY: build-vulture-whitelistpy
