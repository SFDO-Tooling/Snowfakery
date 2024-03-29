from io import StringIO
import pathlib
from unittest import mock
from snowfakery.output_streams import DebugOutputStream

from snowfakery.data_generator import generate

dnd_test = pathlib.Path(__file__).parent / "CharacterGenTest.yml"
data_imports = pathlib.Path(__file__).parent / "BDI_generator.yml"
standard_objects = pathlib.Path(__file__).parent / "gen_sf_standard_objects.yml"
npsp_standard_objects = pathlib.Path(__file__).parent / "gen_npsp_standard_objects.yml"
simple_salesforce = (
    pathlib.Path(__file__).parent / ".." / "examples" / "basic-salesforce.recipe.yml"
)


def find_row(row_type, compare, calls):
    for call in calls:
        args = call[1]
        call_row_type, row_values = args
        if call_row_type == row_type and all(
            compare[key] == row_values[key] for key in compare.keys()
        ):
            return row_values  # return the args


class TestParseAndOutput:
    def test_d_and_d(self, generated_rows):
        with open(dnd_test) as open_yaml_file:
            generate(
                open_yaml_file=open_yaml_file,
                user_options={"num_fighters": 1, "num_druids": 2},
            )
        calls = generated_rows.mock_calls
        assert find_row("Equipment", {"id": 1}, calls)
        assert find_row("Druid", {"id": 1, "Hit Points": mock.ANY}, calls)
        assert find_row("Druid", {"id": 2, "Hit Points": mock.ANY}, calls)
        assert find_row("Fighter", {"id": 1, "Name": mock.ANY}, calls)
        assert not find_row("Fighter", {"id": 2, "Name": mock.ANY}, calls)
        assert find_row("Paladin", {"id": 1, "Name": mock.ANY}, calls)

    def test_data_imports(self, generated_rows):
        with open(data_imports) as open_yaml_file:
            generate(open_yaml_file, {"total_data_imports": 4}, None)
        calls = generated_rows.mock_calls
        assert find_row(
            "General_Accounting_Unit__c", {"id": 1, "Name": "Scholarship"}, calls
        )

        assert find_row(
            "DataImport__c", {"id": 1, "Account1_Street__c": "Cordova Street"}, calls
        )

        assert find_row(
            "Account",
            {
                "id": 1,
                "BillingStreet": "Cordova Street",
                "BillingCountry": "Tuvalu",
                "description": "Pre-existing",
                "record_type": "HH_Account",
            },
            calls,
        )

    def test_gen_standard_objects(self, generated_rows):
        with open(standard_objects) as open_yaml_file:
            generate(open_yaml_file, {}, None)

        calls = generated_rows.mock_calls

        assert find_row("Account", {}, calls)
        assert find_row("Contact", {}, calls)
        assert find_row("Opportunity", {}, calls)

    def test_gen_npsp_standard_objects(self, generated_rows):
        with open(npsp_standard_objects) as open_yaml_file:
            generate(open_yaml_file, {}, None)

        calls = generated_rows.mock_calls

        assert find_row("Account", {}, calls)
        assert find_row("Contact", {}, calls)
        assert find_row("Opportunity", {}, calls)

    def test_simple_salesforce(self, generated_rows):
        with open(simple_salesforce) as open_yaml_file:
            generate(open_yaml_file, {}, None)

        calls = generated_rows.mock_calls

        assert find_row("Account", {}, calls)
        assert find_row("Contact", {}, calls)
        assert find_row("Opportunity", {}, calls)

    def test_parse_nested_macros(self):
        f = StringIO()
        filename = (
            pathlib.Path(__file__).parent.parent / "examples/nested_macros.recipe.yml"
        )
        with open(filename) as yaml:
            generate(yaml, output_stream=DebugOutputStream(f))
        assert (
            f.getvalue()
            == pathlib.Path(str(filename).replace(".yml", ".out")).read_text()
        )
