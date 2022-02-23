from io import StringIO

import pytest

from snowfakery import data_gen_exceptions as exc
from snowfakery import generate_data


class TestVersion:
    def test_version_3_date_handling(self, generated_rows):
        yaml = """
            - snowfakery_version: 3
            - object: Example
              fields:
                y: ${{datetime(year=2000, month=1, day=1)}}
                z: ${{y.date()}}"""
        generate_data(StringIO(yaml))
        assert generated_rows.table_values("Example", 0, "z")

    def test_version_2_date_handling(self, generated_rows):
        yaml = """
            - snowfakery_version: 2
            - object: Example
              fields:
                y: ${{datetime(year=2000, month=1, day=1)}}
                z: ${{y + "XYZZY"}}"""
        generate_data(StringIO(yaml))
        assert generated_rows.table_values("Example", 0, "z").endswith("XYZZY")

    def test_conflicting_versions(self, generated_rows):
        yaml = """
            - snowfakery_version: 2
            - snowfakery_version: 3
            - object: Example
              fields:
                y: ${{datetime(year=2000, month=1, day=1)}}
                z: ${{y + "XYZZY"}}"""
        with pytest.raises(exc.DataGenSyntaxError) as e:
            generate_data(StringIO(yaml))
        assert "conflicting versions" in str(e.value)

    def test_conflicting_unknown_version(self, generated_rows):
        yaml = """
            - snowfakery_version: 4
            - object: Example
        """
        with pytest.raises(exc.DataGenSyntaxError) as e:
            generate_data(StringIO(yaml))
        assert "Version" in str(e.value)
