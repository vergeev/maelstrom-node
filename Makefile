# I primarily use it for ":make" from inside Vim
all: mypy check format test

mypy:
	@uv run mypy . --no-error-summary
# Does not really for vim quickfix list out-of-the-box,
# so I do not include it in "all"
pyrefly:
	@uv run pyrefly check --output-format min-text --progress-bar no --summary=none
check:
	@uv run ruff check -q --output-format concise
format:
	@uv run ruff format -q --output-format concise
run:
	@uv run python main.py
test:
	@uv run python -m pytest -q
