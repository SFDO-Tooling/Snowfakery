import sys
from pathlib import Path
from unittest.mock import patch

import pytest

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
