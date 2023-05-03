# Test a dev installation succeeds

set -e

ROOTDIR=/tmp/test_sf_install
rm -rf $ROOTDIR
mkdir $ROOTDIR
pushd $ROOTDIR
git clone https://github.com/SFDO-Tooling/Snowfakery
git clone https://github.com/SFDO-Tooling/CumulusCI
python3.10 -m venv $ROOTDIR/snowfakery_venv
source $ROOTDIR/snowfakery_venv/bin/activate
cd Snowfakery
make dev-install
pip install -e ../CumulusCI
export PYTHONPATH=.
pytest
popd