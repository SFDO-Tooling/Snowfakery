rm -rf /tmp/Snowfakery /tmp/CumulusCI /tmp/snowfakery_venv
pushd /tmp
git clone https://github.com/SFDO-Tooling/Snowfakery
git clone https://github.com/SFDO-Tooling/CumulusCI
python3.10 -m venv /tmp/snowfakery_venv
source /tmp/snowfakery_venv/bin/activate
cd Snowfakery
make dev-install
pip install -e ../CumulusCI
export PYTHONPATH=.
pytest
popd