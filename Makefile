all: ruff-format ruff-check mypy-check pyrefly-check test run

mypy-check:
	@uv run mypy . --no-error-summary
pyrefly-check:
	@uv run pyrefly check --output-format min-text --progress-bar no --summary=none
ruff-check:
	@uv run ruff check -q --output-format concise
ruff-format:
	@uv run ruff format -q --output-format concise
run:
	@uv run python -m src.main
test:
	@uv run python -m pytest -q
