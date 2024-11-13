update-deps:
	uv lock --upgrade
	uv pip compile docs/requirements.in -o docs/requirements.txt --universal -p 3.11

dev-install:
	uv sync

# set SF_MKDOCS_BUILD_LOCALES=False to skip building all locales
docs:		.FORCE
	mkdocs build --clean --site-dir build/html --config-file mkdocs.yml

coverage:
	uv run pytest --cov --cov-report=html
	open htmlcov/index.html

.FORCE:
