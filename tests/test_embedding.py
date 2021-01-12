from tempfile import TemporaryDirectory
from pathlib import Path
import yaml

from snowfakery import generate_data


class TestEmbedding:
    def test_simple_embedding(self):
        generate_data("tests/gender_conditional.yml")

    def test_embedding_dburl(self):
        with TemporaryDirectory() as t:
            dbpath = Path(t) / "foo.db"
            dburl = f"sqlite:///{dbpath}"
            generate_data("tests/gender_conditional.yml", dburl=dburl)
            assert dbpath.exists()

    def test_arguments(self):
        with TemporaryDirectory() as t:
            outfile = Path(t) / "foo.txt"
            continuation = Path(t) / "out.yml"
            generate_data(
                yaml_file="examples/company.yml",
                user_options={"A": "B"},
                target_number=(20, "Employee"),
                debug_internals=True,
                output_format="json",
                output_file=outfile,
                generate_continuation_file=continuation,
            )
            assert outfile.exists()
            assert continuation.exists()
            with continuation.open() as f:
                assert yaml.safe_load(f)

    def test_continuation_as_open_file(self):
        with TemporaryDirectory() as t:
            outfile = Path(t) / "foo.json"
            continuation = Path(t) / "out.yml"
            with open(continuation, "w") as cont:
                generate_data(
                    yaml_file="examples/company.yml",
                    target_number=(20, "Employee"),
                    debug_internals=False,
                    output_file=outfile,
                    generate_continuation_file=cont,
                )
            assert outfile.exists()
            assert continuation.exists()
            with continuation.open() as f:
                assert yaml.safe_load(f)
