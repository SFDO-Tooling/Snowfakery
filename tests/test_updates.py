from tempfile import TemporaryDirectory
from pathlib import Path
from snowfakery.cli import generate_cli


class TestUpdates:
    def test_updates_through_cli(self):
        sample_yaml = "tests/test_updates.py"
        with TemporaryDirectory() as t:
            generate_cli.main(
                [
                    sample_yaml,
                    "--output-file",
                    Path(t) / "foo.csv",
                    "--update-input-file",
                ],
                standalone_mode=False,
            )
