all: mypy check format

mypy:
	@uv run mypy .
check:
	@uv run ruff check -s
format:
	@uv run ruff format -s
run:
	@uv run python main.py
