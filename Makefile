all: mypy check format test

mypy:
	@uv run mypy . --no-error-summary
check:
	@uv run ruff check -q --output-format concise
format:
	@uv run ruff format -q --output-format concise
run:
	@uv run python main.py
test:
	@uv run python -m pytest -q
