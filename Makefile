setup:
	uv venv && uv sync
	@echo "activate: source ./.venv/bin/activate"

db_open:
	open -a TablePlus $$DATABASE_URL

clean:
	rm -rf *.egg-info
	rm -rf .venv
