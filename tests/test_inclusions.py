import pathlib
import pytest

from snowfakery.data_generator import generate
from snowfakery.data_gen_exceptions import DataGenError


class TestReferences:
    def test_included_file(self, generated_rows):
        include_parent = pathlib.Path(__file__).parent / "include_parent.yml"
        with open(include_parent) as f:
            generate(f, {}, None)

        generated_rows.assert_called_with(
            "Account",
            {"id": 1, "name": "Default Company Name", "ShippingCountry": "Canada"},
        )

    def test_failed_include_file(self, generated_rows):
        failed_include = pathlib.Path(__file__).parent / "include_bad_parent.yml"
        with pytest.raises(DataGenError):
            with open(failed_include) as f:
                generate(f)
