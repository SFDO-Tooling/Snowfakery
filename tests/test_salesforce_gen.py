from base64 import b64decode
from io import StringIO

from snowfakery import generate_data
from tests.test_with_cci import skip_if_cumulusci_missing

import pytest


class TestSalesforceGen:
    def test_content_version(self, generated_rows):
        content_version = "examples/base64_file.recipe.yml"
        generate_data(content_version)
        for i in range(0, 2):
            b64data = generated_rows.table_values("ContentVersion", i)["VersionData"]
            rawdata = b64decode(b64data)
            assert rawdata.startswith(b"%PDF-1.3")
            assert b"Helvetica" in rawdata

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
