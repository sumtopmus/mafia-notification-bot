.PHONY: run debug clean-cache clean-logs clean-data

run: clean-cache
	@ENV_FOR_DYNACONF=production python src/main.py

debug: clean-all
	@python src/main.py

clean-all: clean-cache clean-logs clean-data

clean-cache:
	@rm -rf src/__pycache__
	@rm -rf src/handlers/__pycache__

clean-logs:
	@rm -rf logs

clean-data:
	@rm -rf data
