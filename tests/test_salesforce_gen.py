from base64 import b64decode

from snowfakery import generate_data


class TestSalesforceGen:
    def test_content_version(self, generated_rows):
        content_version = "examples/base64_file.recipe.yml"
        generate_data(content_version)
        for i in range(0, 2):
            b64data = generated_rows.table_values("ContentVersion", i)["VersionData"]
            rawdata = b64decode(b64data)
            assert rawdata.startswith(b"%PDF-1.3")
            assert b"Helvetica" in rawdata
