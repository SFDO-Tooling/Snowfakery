make
pip install ./pyodide-build
rm -rf packages/sqlalchemy/ packages/markupsafe/ packages/python_baseconv/
# Based on https://pyodide.org/en/stable/development/new-packages.html
python -m pyodide_build mkpkg sqlalchemy --version 1.4.36
python -m pyodide_build mkpkg python_baseconv --version 1.2.2
pushd packages/sqlalchemy/; python -m pyodide_build buildpkg meta.yaml ; popd
pushd packages/python_baseconv/; python -m pyodide_build buildpkg meta.yaml ; popd
