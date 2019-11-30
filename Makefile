mypy:
	@mypy .
.PHONY: mypy

test:
	@pytest tests
.PHONY: test
