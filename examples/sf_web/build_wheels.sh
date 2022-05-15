SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )

mkdir /tmp/build_wheels
pushd /tmp/build_wheels

git clone https://github.com/pyodide/pyodide.git
cd pyodide
cp $SCRIPT_DIR/build_wheels_inside_docker.sh .
./run_docker ./build_wheels_inside_docker.sh

popd
PACKAGEDIR=/tmp/build_wheels/pyodide/packages
cp $PACKAGEDIR/sqlalchemy/dist/SQLAlchemy*.whl examples/sf_web
# cp $PACKAGEDIR/markupsafe/dist/MarkupSafe-*.whl examples/sf_web
cp $PACKAGEDIR/python_baseconv/dist/python_baseconv*.whl examples/sf_web