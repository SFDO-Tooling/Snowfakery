from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from sqlalchemy import create_engine


from snowfakery.cli import generate_cli

try:
    import cumulusci
except ImportError:
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
