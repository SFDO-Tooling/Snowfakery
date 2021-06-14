update-deps:
	pip-compile --upgrade --allow-unsafe requirements/prod.in
	pip-compile --upgrade --allow-unsafe requirements/dev.in

dev-install:
	pip-sync requirements/*.txt

# set SF_MKDOCS_BUILD_LOCALES=False to skip building all locales
docs:		.FORCE
	python -m mkdocs build --clean --site-dir build/html --config-file mkdocs.yml

.FORCE: