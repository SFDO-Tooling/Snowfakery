import sys
from pathlib import Path
from unittest.mock import patch
from contextlib import contextmanager

import pytest
import yaml
from sqlalchemy import create_engine

try:
    import cumulusci
except ImportError:
    cumulusci = None

if cumulusci:
    from conftest_extras_w_cci import *  # noQA

else:
    print("CumulusCI/Snowfakery Integration Tests will be skipped.")

sys.path.insert(0, str(Path(__file__).parent.parent))


@pytest.fixture(scope="function")
def generated_rows(request):
    def row_values(index, value):
        return mockobj.mock_calls[index][1][1][value]

    def table_values(tablename, index, field=None):
        """Look up a value from a table."""
        index = index - 1  # use 1-based indexing like Snowfakery does

        # create and cache a dict of table names to lists of rows
        if type(mockobj._index) != dict:
            mockobj._index = {}
            for row in mockobj.mock_calls:
                table = row[1][0]
                mockobj._index.setdefault(table, []).append(row[1][1])

        if field:  # return just one field
            return mockobj._index[tablename][index][field]
        else:  # return a full row
            return mockobj._index[tablename][index]

    with patch(
        "snowfakery.output_streams.DebugOutputStream.write_single_row"
    ) as mockobj:
        mockobj.row_values = row_values
        mockobj.table_values = table_values
        yield mockobj


@pytest.fixture(scope="function")
def disable_typeguard():
    with patch("typeguard.check_argument_types", lambda *args, **kwargs: ...):
        yield


@pytest.fixture(scope="function")
def generate_in_tmpdir(tmpdir):
    from snowfakery import generate_data

    tmpdir = Path(tmpdir)

    @contextmanager
    def doit(recipe_data, *args, **kwargs):
        db = tmpdir / "testdb.db"
        dburl = f"sqlite:///{db}"
        recipe = tmpdir / "recipe.yml"
        mapping_file = tmpdir / "mapping.yml"
        recipe.write_text(recipe_data)
        generate_data(
            recipe,
            *args,
            generate_cci_mapping_file=mapping_file,
            dburl=dburl,
            should_create_cci_record_type_tables=True,
            **kwargs,
        )
        mapping = yaml.safe_load(mapping_file.read_text())
        e = create_engine(dburl)
        with e.connect() as connection:
            yield mapping, connection

    return doit


@pytest.fixture(scope="session")
def snowfakery_rootdir():
    return Path(__file__).parent.parent
