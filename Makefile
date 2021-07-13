update-deps:
	pip-compile --upgrade --allow-unsafe requirements/prod.in
	pip-compile --upgrade --allow-unsafe requirements/dev.in

dev-install:
	pip install --upgrade pip-tools
	pip-sync requirements/*.txt
	pip install -e .

# set SF_MKDOCS_BUILD_LOCALES=False to skip building all locales
docs:		.FORCE
	python tools/docs_samples.py
	python -m mkdocs build --clean --site-dir build/html --config-file mkdocs.yml

.FORCE: