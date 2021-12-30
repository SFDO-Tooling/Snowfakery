from tempfile import TemporaryDirectory
from pathlib import Path
from snowfakery.cli import generate_cli


class TestUpdates:
    def test_updates_through_cli(self):
        sample_yaml = "examples/update_contexts.recipe.yml"
        with TemporaryDirectory() as t:
            generate_cli.main(
                [
                    sample_yaml,
                    "--output-format",
                    "csv",
                    "--output-folder",
                    Path(t),
                    "--update-input-file",
                    Path("examples/datasets/addresses.csv"),
                ],
                standalone_mode=False,
            )
