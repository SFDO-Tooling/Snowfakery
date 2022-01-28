from glob import glob
from jsonschema import validate
from jsonschema.exceptions import ValidationError
import json
import pytest
import yaml

skippables = ["load.yml", "mapping_"]


class TestSchema:
    def test_schema(self):
        with open("schema/snowfakery_recipe.jsonschema.json") as f:
            schema = json.load(f)
        files = glob("tests/*.yml") + glob("examples/*.yml")
        files = [
            f for f in files if not any(skippable in f for skippable in skippables)
        ]
        for file in files:
            with open(file) as f:
                data = yaml.safe_load(f)
                print(file)
                validate(instance=data, schema=schema)
                print("Success", file)

    def test_bad_recipes(self):
        with open("schema/snowfakery_recipe.jsonschema.json") as f:
            schema = json.load(f)
        files = glob("tests/errors/*.yml")

        for file in files:
            with open(file) as f:
                data = yaml.safe_load(f)
                print(file)
                with pytest.raises(ValidationError):
                    validate(instance=data, schema=schema)
                print("Success", file)
