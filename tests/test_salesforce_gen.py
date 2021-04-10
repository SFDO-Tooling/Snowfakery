from base64 import b64decode

from snowfakery import generate_data


class TestSalesforceGen:
    def test_content_version(self, generated_rows):
        content_version = "examples/salesforce/ContentVersion.recipe.yml"
        generate_data(content_version)
        b64data = generated_rows.table_values("ContentVersion", 0)["VersionData"]
        rawdata = b64decode(b64data)
        assert rawdata.startswith(b"%PDF-1.3")
        assert b"Helvetica" in rawdata
