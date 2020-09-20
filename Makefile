# See: https://blog.thapaliya.com/posts/well-documented-makefiles/
help: ##- Show this help message.
	@awk 'BEGIN {FS = ":.*##-"; printf "usage: make \033[36m<target>\033[0m\n\nTargets:\n"} /^[a-zA-Z0-9_-]+:.*##-/ { printf "  \033[36m%-29s\033[0m %s\n", $$1, $$2 }' $(MAKEFILE_LIST)
.PHONY: help

# ------------------------------------------------------------------------------

.venv:
	@python3.6 -m venv .venv

.venv/.devinstall: .venv
	@.venv/bin/pip install --upgrade pip setuptools wheel
	@grep git+git setup.cfg | awk '{ gsub (" ", "", $$0); print}' | xargs -r .venv/bin/pip install --upgrade
	@.venv/bin/pip install -e .[test,dev]
	@touch .venv/.devinstall

devinstall: ##- Install the project in editable mode with all test and dev dependencies (in a virtual environment).
	@rm -f .venv/.devinstall
	@make --silent .venv/.devinstall
.PHONY: devinstall

devinstall-localdeps: .venv/.devinstall ##- Install dependencies developed together with this project in editable mode.
	@if [ -z "$(DIR)" ]; then \
		echo "Directory from which to install dependencies not set. Use like this: make devinstall-localdeps DIR=.."; \
	else \
		.venv/bin/pip install \
			-e $(DIR)/nasty-typeshed \
			-e $(DIR)/nasty-utils \
		; \
	fi
.PHONY: devinstall-localdeps

# ------------------------------------------------------------------------------

test: test-pytest ##- Run all tests and report test coverage.
.PHONY: test

test-pytest: .venv/.devinstall ##- Run all tests in the currently active environment.
	@.venv/bin/pytest --cov --cov-report= --cov-context test --html tests-report.html --self-contained-html
	@.venv/bin/coverage html --dir tests-coverage
	@.venv/bin/coverage report
.PHONY: test-pytest

test-nox: .venv/.devinstall ##- Run all tests against all supported Python versions (in separate environments).
	@.venv/bin/coverage erase
	@.venv/bin/nox
	@.venv/bin/coverage html --dir tests-coverage
	@.venv/bin/coverage report
.PHONY: test-nox

# ------------------------------------------------------------------------------

check: check-flake8 check-mypy check-vulture check-isort check-black ##- Run linters and perform static type-checking.
.PHONY: check

# Not using the following in `check`-rule because it always spams output, even
# in case of success (no quiet flag) and because most of the checking is already
# performed by flake8.
check-autoflake: .venv/.devinstall ##- Check for unused imports and variables.
	@.venv/bin/autoflake --check --remove-all-unused-imports --remove-duplicate-keys --remove-unused-variables --recursive .
.PHONY: check-autoflake

check-flake8: .venv/.devinstall ##- Run linters.
	@.venv/bin/flake8 src tests *.py
.PHONY: check-flake8

check-mypy: .venv/.devinstall ##- Run static type-checking.
	@.venv/bin/mypy src .
.PHONY: check-mypy

check-vulture: .venv/.devinstall ##- Check for unused code.
	@.venv/bin/vulture src tests *.py
.PHONY: check-vulture

check-isort: .venv/.devinstall ##- Check if imports are sorted correctly.
	@.venv/bin/isort --check-only --quiet .
.PHONY: check-isort

check-black: .venv/.devinstall ##- Check if code is formatted correctly.
	@.venv/bin/black --check .
.PHONY: check-black

# ------------------------------------------------------------------------------

format: format-licenseheaders format-autoflake format-isort format-black ##- Auto format all code.
.PHONY: format

format-licenseheaders: .venv/.devinstall ##- Prepend license headers to all code files.
	@.venv/bin/licenseheaders --tmpl LICENSE.header --years 2019-2020 --owner "Lukas Schmelzeisen" --dir src
	@.venv/bin/licenseheaders --tmpl LICENSE.header --years 2019-2020 --owner "Lukas Schmelzeisen" --dir tests
.PHONY: format-licenseheaders

format-autoflake: .venv/.devinstall ##- Remove unused imports and variables.
	@.venv/bin/autoflake --in-place --remove-all-unused-imports --remove-duplicate-keys --remove-unused-variables --recursive .
.PHONY: format-autoflake

format-isort: .venv/.devinstall ##- Sort all imports.
	@.venv/bin/isort --quiet .
.PHONY: format-isort

format-black: .venv/.devinstall ##- Format all code.
	@.venv/bin/black .
.PHONY: format-black

# ------------------------------------------------------------------------------

publish: publish-setuppy publish-twine-check ##- Build and check source and binary distributions.
.PHONY: publish

publish-setuppy: .venv/.devinstall ##- Build source and binary distributions.
	@rm -rf build dist
	@.venv/bin/python setup.py sdist bdist_wheel
.PHONY: publish-setuppy

publish-twine-check: .venv/.devinstall ##- Check source and binary distributions for upload.
	@.venv/bin/twine check dist/*
.PHONY: publish-twine-check

publish-upload-testpypi: .venv/.devinstall ##- Upload to TestPyPI.
	@.venv/bin/twine upload --repository-url https://test.pypi.org/legacy/ dist/*
.PHONY: publish-twine-upload-testpypi

publish-upload-pypi: .venv/.devinstall ##- Upload to PyPI.
	@.venv/bin/twine upload dist/*
.PHONY: publish-twine-upload

# ------------------------------------------------------------------------------

clean: ##- Remove all created cache/build files, test/coverage reports, and virtual environments.
	@rm -rf .coverage* .eggs .mypy_cache .pytest_cache .nox .venv build dist src/*/_version.py src/*.egg-info tests/util/.requests_cache.jsonl tests-coverage tests-report.html
	@find . -type d -name __pycache__ -exec rm -r {} +
.PHONY: clean

# ------------------------------------------------------------------------------

build-vulture-whitelistpy:  .venv/.devinstall ##- Regenerate vulture whitelist (list of currently seemingly unused code that will not be reported).
	@.venv/bin/vulture src tests *.py --make-whitelist > vulture-whitelist.py || true
.PHONY: build-vulture-whitelistpy
