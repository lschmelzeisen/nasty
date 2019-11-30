mypy:
	@mypy .
.PHONY: mypy

test:
	@pytest tests
.PHONY: test

dev-environ:
	PIPENV_VENV_IN_PROJECT=1 pipenv install --dev
.PHONY: dev-environ
