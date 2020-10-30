from tempfile import TemporaryDirectory
from pathlib import Path

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
            generate_data(
                yaml_file="tests/gender_conditional.yml",
                option=[("A", "B")],
                target_number=(20, "A"),
                debug_internals=True,
                output_format="json",
                output_file=outfile,
            )
