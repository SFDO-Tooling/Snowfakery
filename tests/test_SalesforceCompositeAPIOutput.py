from io import StringIO
from unittest.mock import patch

from snowfakery.data_generator import generate
from snowfakery.data_generator_runtime import StoppingCriteria
from snowfakery.experimental.SalesforceCompositeAPIOutput import Bundle
import json

## Fill this out when it isn't experimental anymore


class TestSalesforceCompositeAPIOutput:
    @patch("snowfakery.experimental.SalesforceCompositeAPIOutput.MAX_BATCH_SIZE", 5)
    def test_composite(self):
        out = StringIO()
        output_stream = Bundle(out)
        with open("examples/basic-salesforce.recipe.yml") as f:
            generate(
                f, {}, output_stream, stopping_criteria=StoppingCriteria("Account", 15)
            )
        output_stream.close()
        data = json.loads(out.getvalue())
        assert data["bundle_format"] == 1
        assert len(data["data"]) == 10
