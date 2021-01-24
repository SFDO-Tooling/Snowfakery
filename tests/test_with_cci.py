from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch
from io import StringIO

from sqlalchemy import create_engine

import pytest

from snowfakery.cli import generate_cli
from snowfakery.data_generator import generate
from snowfakery.data_gen_exceptions import DataGenError
from snowfakery import generate_data

try:
    import cumulusci
except ImportError:
    cumulusci = False

sample_mapping_yaml = Path(__file__).parent / "mapping_vanilla_sf.yml"
sample_accounts_yaml = Path(__file__).parent / "gen_sf_standard_objects.yml"

sample_yaml = Path(__file__).parent / "include_parent.yml"


skip_if_cumulusci_missing = pytest.mark.skipif(
    not hasattr(cumulusci, "api"), reason="CumulusCI not installed"
)


class Test_CLI_CCI:
    @skip_if_cumulusci_missing
    def test_mapping_file(self):
        with TemporaryDirectory() as t:
            url = f"sqlite:///{t}/foo.db"
            generate_cli.main(
                [
                    "--cci-mapping-file",
                    str(sample_mapping_yaml),
                    str(sample_accounts_yaml),
                    "--dburl",
                    url,
                ],
                standalone_mode=False,
            )

            engine = create_engine(url)
            with engine.connect() as connection:
                result = list(connection.execute("select * from Account"))
                assert result[0]["id"] == 1
                assert result[0]["BillingCountry"] == "Canada"


class FakeSimpleSalesforce:
    def __init__(self, query_responses):
        self.query_responses = query_responses

    def query(self, query: str):
        try:
            return self.query_responses[query]
        except KeyError:
            raise KeyError(f"No mock response found for Salesforcce query `{query}`")


fake_sf_client = FakeSimpleSalesforce(
    {
        "SELECT count() FROM Account": {"totalSize": 10},
        "Select Id FROM Account LIMIT 1 OFFSET 0": {"records": [{"Id": "FAKEID0"}]},
        "Select Id FROM Account LIMIT 1 OFFSET 5": {"records": [{"Id": "FAKEID5"}]},
    }
)


class TestSOQLNoCCI:
    @patch(
        "snowfakery.standard_plugins.salesforce.Salesforce.Functions._sf",
        wraps=fake_sf_client,
    )
    @patch("snowfakery.standard_plugins.salesforce.randrange", lambda *arg, **kwargs: 5)
    def test_soql_plugin_random(self, fake_sf_client, generated_rows):
        yaml = """
            - plugin: snowfakery.standard_plugins.salesforce.Salesforce
            - object: Contact
              fields:
                FirstName: Suzy
                LastName: Salesforce
                AccountId:
                    Salesforce.query_random: Account
        """
        generate(StringIO(yaml), plugin_options={"orgname": "blah"})
        assert fake_sf_client.mock_calls
        assert generated_rows.row_values(0, "AccountId") == "FAKEID5"

    @patch(
        "snowfakery.standard_plugins.salesforce.Salesforce.Functions._sf",
        wraps=fake_sf_client,
    )
    @patch("snowfakery.standard_plugins.salesforce.randrange", lambda *arg, **kwargs: 5)
    def test_soql_plugin_record(self, fake_sf_client, generated_rows):
        yaml = """
            - plugin: snowfakery.standard_plugins.salesforce.Salesforce
            - object: Contact
              fields:
                FirstName: Suzy
                LastName: Salesforce
                AccountId:
                    Salesforce.query_record: Account
        """
        generate(StringIO(yaml), plugin_options={"orgname": "blah"})
        assert fake_sf_client.mock_calls
        assert generated_rows.row_values(0, "AccountId") == "FAKEID0"


class TestSOQLWithCCI:
    @patch("snowfakery.standard_plugins.salesforce.randrange", lambda *arg, **kwargs: 5)
    @pytest.mark.vcr()
    @skip_if_cumulusci_missing
    def test_soql(self, org_config, generated_rows):
        yaml = """
            - plugin: snowfakery.standard_plugins.salesforce.Salesforce
            - object: Contact
              fields:
                FirstName: Suzy
                LastName: Salesforce
                AccountId:
                    Salesforce.query_random: Account
            - object: Contact
              fields:
                FirstName: Sammy
                LastName: Salesforce
                AccountId:
                    Salesforce.query_random: Account
        """
        assert org_config.name
        generate(StringIO(yaml), plugin_options={"orgname": org_config.name})

    @skip_if_cumulusci_missing
    def test_missing_orgname(self):
        yaml = """
            - plugin: snowfakery.standard_plugins.salesforce.Salesforce
            - object: Contact
              fields:
                AccountId:
                    Salesforce.query_random: Account
        """
        with pytest.raises(DataGenError):
            generate(StringIO(yaml), {})

    @patch("snowfakery.standard_plugins.salesforce.randrange", lambda *arg, **kwargs: 5)
    @skip_if_cumulusci_missing
    @pytest.mark.vcr()
    def test_example_through_api(self, generated_rows, org_config):
        filename = (
            Path(__file__).parent.parent / "examples/salesforce_soql_example.recipe.yml"
        )
        generate_data(filename, plugin_options={"orgname": org_config.name})
        assert generated_rows.mock_calls

    def test_cci_not_available(self):
        filename = (
            Path(__file__).parent.parent / "examples/salesforce_soql_example.recipe.yml"
        )
        with unittest.mock.patch(
            "snowfakery.standard_plugins.salesforce._get_sf_connection"
        ) as conn:
            conn.side_effect = ImportError(
                "cumulusci module cannot be loaded by snowfakery"
            )
            with pytest.raises(Exception, match="cumulusci module cannot be loaded"):
                generate_data(filename, plugin_options={"orgname": "None"})
