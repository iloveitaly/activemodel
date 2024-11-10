setup:
	uv venv && uv sync
	@echo "activate: source ./.venv/bin/activate"

clean:
	rm -rf *.egg-info
	rm -rf .venv
