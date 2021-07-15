from base64 import b64decode

import pytest
from snowfakery import generate_data
from snowfakery.standard_plugins.Salesforce import SalesforceConnection
from snowfakery import data_gen_exceptions as exc


class TestSalesforceGen:
    def test_content_version(self, generated_rows):
        content_version = "examples/salesforce/ContentVersion.recipe.yml"
        generate_data(content_version)
        b64data = generated_rows.table_values("ContentVersion", 0)["VersionData"]
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
