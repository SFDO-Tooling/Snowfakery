from io import StringIO
from unittest.mock import patch

from snowfakery.data_generator import generate
from snowfakery.data_generator_runtime import StoppingCriteria
from snowfakery.experimental.DataPack import (
    DataPack,
    ApexDataPack,
    SalesforceCompositeAPIOutput,
)
import json

## Fill this out when it isn't experimental anymore


class TestSalesforceCompositeAPIOutput:
    @patch("snowfakery.experimental.DataPack.MAX_BATCH_SIZE", 10)
    def test_composite(self):
        out = StringIO()
        output_stream = DataPack(out)
        with open("examples/basic-salesforce.recipe.yml") as f:
            generate(
                f, {}, output_stream, stopping_criteria=StoppingCriteria("Account", 15)
            )
        output_stream.close()
        data = json.loads(out.getvalue())
        assert data["datapack_format"] == 1
        assert len(data["data"]) == 8
        single_payload = json.loads(data["data"][0])
        print(single_payload)
        assert single_payload["graphs"][0]["compositeRequest"][0]["method"] == "POST"

    def test_reference(self):
        out = StringIO()
        output_stream = SalesforceCompositeAPIOutput(out)
        with open("examples/basic-salesforce.recipe.yml") as f:
            generate(f, {}, output_stream)
        output_stream.close()
        print(out.getvalue())
        data = json.loads(out.getvalue())
        assert (
            data["graphs"][0]["compositeRequest"][-1]["body"]["AccountId"]
            == "@{Account_2.id}"
        )

    @patch("snowfakery.experimental.DataPack.MAX_BATCH_SIZE", 50)
    def test_composite_upsert(self):
        out = StringIO()
        output_stream = DataPack(out)
        with open("tests/upsert-2.yml") as f:
            generate(
                f, {}, output_stream, stopping_criteria=StoppingCriteria("Account", 50)
            )
        output_stream.close()
        data = json.loads(out.getvalue())
        assert data["datapack_format"] == 1
        single_payload = json.loads(data["data"][1])
        assert single_payload["graphs"][0]["compositeRequest"][-1]["method"] == "PATCH"

    def test_apex(self):
        out = StringIO()
        output_stream = ApexDataPack(out)
        with open("examples/basic-salesforce.recipe.yml") as f:
            generate(
                f, {}, output_stream, stopping_criteria=StoppingCriteria("Account", 50)
            )
        output_stream.close()
        out = out.getvalue()
        assert out.startswith("String json_data")
