from tempfile import TemporaryDirectory
from pathlib import Path
from unittest.mock import call, ANY
import pytest

from snowfakery.cli import generate_cli
from snowfakery import generate_data
from snowfakery.data_gen_exceptions import DataGenSyntaxError


class TestUpdates:
    def test_updates_through_cli(self):
        sample_yaml = "examples/updates/update_contacts.recipe.yml"
        with TemporaryDirectory() as t:
            generate_cli.main(
                [
                    sample_yaml,
                    "--output-format",
                    "csv",
                    "--output-folder",
                    Path(t),
                    "--update-input-file",
                    Path("examples/datasets/addresses.csv"),
                ],
                standalone_mode=False,
            )
            assert Path(sample_yaml).exists()
            lines_in_orig = [
                line for line in Path("examples/datasets/addresses.csv").open() if line
            ]
            lines_in_output = [line for line in Path(t, "Contact.csv").open() if line]
            assert len(lines_in_orig) == len(lines_in_output)

    def test_updates_through_api(self, generated_rows):
        generate_data(
            "examples/updates/update_contacts.recipe.yml",
            update_input_file="examples/datasets/addresses.csv",
        )
        print(generated_rows.mock_calls)
        assert generated_rows.mock_calls == _expected_data(ANY)

    def test_updates_bad_recipe_format(self):
        with pytest.raises(DataGenSyntaxError):
            generate_data(
                "examples/basic-salesforce.recipe.yml",
                update_input_file="examples/datasets/addresses.csv",
            )

    def test_updates_with_options(self, generated_rows):
        generate_data(
            "examples/updates/update_contacts_with_options.recipe.yml",
            update_input_file="examples/datasets/addresses.csv",
            user_options={"FirstName": "Jane"},
        )
        assert generated_rows.mock_calls == _expected_data("Jane")


def _expected_data(firstname):
    return [
        call(
            "Contact",
            {
                "id": 1,
                "FirstName": firstname,
                "LastName": ANY,
                "BillingStreet": "420 Kings Ave",
                "BillingCity": "Burnaby",
                "BillingState": "Texas",
                "BillingPostalCode": 85633,
                "BillingCountry": "US",
                "Oid": "0032D00000V6UvUQAV",
            },
        ),
        call(
            "Contact",
            {
                "id": 2,
                "FirstName": firstname,
                "LastName": ANY,
                "BillingStreet": "421 Granville Street",
                "BillingCity": "White Rock",
                "BillingState": "Texas",
                "BillingPostalCode": 85633,
                "BillingCountry": "US",
                "Oid": "032D00000V6UvVQAV",
            },
        ),
        call(
            "Contact",
            {
                "id": 3,
                "FirstName": firstname,
                "LastName": ANY,
                "BillingStreet": "422 Kingsway Road",
                "BillingCity": "Richmond",
                "BillingState": "Texas",
                "BillingPostalCode": 85633,
                "BillingCountry": "US",
                "Oid": "032D00000V6UvfQAF",
            },
        ),
    ]
