from pathlib import Path
from tempfile import NamedTemporaryFile, TemporaryDirectory
import unittest
from click import ClickException
from sqlalchemy import create_engine


from snowfakery.cli import generate_cli, eval_arg

try:
    import cumulusci
except:
    cumulusci = False

sample_mapping_yaml = Path(__file__).parent / "mapping_vanilla_sf.yml"
sample_accounts_yaml = Path(__file__).parent / "gen_sf_standard_objects.yml"

sample_yaml = Path(__file__).parent / "include_parent.yml"


class Test_CLI_CCI(unittest.TestCase):
    @unittest.skipUnless(cumulusci, "CumulusCI not installed")
    def test_mapping_file(self):
        with TemporaryDirectory() as t:
            url = f"sqlite:///{t}/foo.db"
            generate_cli.main(
                [
                    "--cci-mapping-file",
                    str(sample_mapping_yaml),
                    str(sample_accounts_yaml),
                    "--dburl",
                    url,
                ],
                standalone_mode=False,
            )

            engine = create_engine(url)
            connection = engine.connect()
            result = list(connection.execute("select * from Account"))
            assert result[0]["id"] == 1
            assert result[0]["BillingCountry"] == "Canada"

    @unittest.skipUnless(cumulusci, "CumulusCI not installed")
    def test_mapping_file_no_dburl(self):
        with self.assertRaises(ClickException):
            generate_cli.main(
                ["--mapping_file", str(sample_mapping_yaml), str(sample_yaml)],
                standalone_mode=False,
            )

    @unittest.skipUnless(cumulusci, "CumulusCI not installed")
    def test_mutually_exclusive(self):
        with self.assertRaises(ClickException) as e:
            with TemporaryDirectory() as t:
                generate_cli.main(
                    [
                        str(sample_yaml),
                        "--dburl",
                        f"csvfile://{t}/csvoutput",
                        "--output-format",
                        "JSON",
                    ],
                    standalone_mode=False,
                )
        assert "mutually exclusive" in str(e.exception)

        with self.assertRaises(ClickException) as e:
            generate_cli.main(
                [
                    str(sample_yaml),
                    "--cci-mapping-file",
                    sample_mapping_yaml,
                    "--output-format",
                    "JSON",
                ],
                standalone_mode=False,
            )
        assert "apping file" in str(e.exception)
