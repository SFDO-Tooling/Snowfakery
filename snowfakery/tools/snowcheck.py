import json
from glob import glob
from pathlib import Path

import click
import yaml
from jsonschema import validate


@click.command()
@click.argument("filespecs", nargs=-1)
def validate_recipe(filespecs):
    schemajson = (
        Path(__file__).parent.parent.parent / "schema/snowfakery_recipe.jsonschema.json"
    )
    assert schemajson.exists()

    with schemajson.open() as f:
        schema = json.load(f)
    files = []
    for filespec in filespecs:
        files.extend(glob(filespec))

    if not files:
        raise click.ClickException("No files matched!")

    for file in files:
        with open(file) as f:
            data = yaml.safe_load(f)
            try:
                validate(instance=data, schema=schema)
            except Exception as e:
                print(f"ERROR with file {file}: {e}")


if __name__ == "__main__":
    validate_recipe()
