from base64 import b64decode
from io import StringIO

import pytest
from snowfakery import generate_data
from snowfakery.standard_plugins.Salesforce import SalesforceConnection
from snowfakery import data_gen_exceptions as exc
from tests.test_with_cci import skip_if_cumulusci_missing


class TestSalesforceGen:
    def test_content_version(self, generated_rows):
        content_version = "examples/base64_file.recipe.yml"
        generate_data(content_version)
        for i in range(0, 2):
            b64data = generated_rows.table_values("ContentVersion", i)["VersionData"]
            rawdata = b64decode(b64data)
            assert rawdata.startswith(b"%PDF-1.3")
            assert b"Helvetica" in rawdata


class TestSalesforceConnection:
    def test_bad_kwargs(self):
        sfc = SalesforceConnection(None)
        with pytest.raises(exc.DataGenError, match="Unknown argument"):
            sfc.compose_query(
                "context_name", fields=["blah"], xyzzy="foo", **{"from": "blah"}
            )


class TestSalesforcePlugin:
    @skip_if_cumulusci_missing
    @pytest.mark.vcr()
    def test_profile_id(self, generated_rows, org_config):
        yaml = """
        - plugin: snowfakery.standard_plugins.Salesforce
        - object: foo
          fields:
            ProfileId:
              Salesforce.ProfileId: Identity User
        """
        generate_data(StringIO(yaml), plugin_options={"org_name": org_config.name})
        assert generated_rows.table_values("foo", 0, "ProfileId").startswith("00e")
