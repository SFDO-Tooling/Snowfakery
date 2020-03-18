import unittest
from unittest import mock
from pathlib import Path
from tempfile import NamedTemporaryFile, TemporaryDirectory
from io import StringIO
import json

import yaml
from click.exceptions import ClickException

from snowfakery.cli import generate_cli, eval_arg
from snowfakery.data_gen_exceptions import DataGenError

sample_yaml = Path(__file__).parent / "include_parent.yml"
bad_sample_yaml = Path(__file__).parent / "include_bad_parent.yml"
sample_accounts_yaml = Path(__file__).parent / "gen_sf_standard_objects.yml"

write_row_path = "snowfakery.output_streams.DebugOutputStream.write_single_row"


class TestGenerateFromCLI(unittest.TestCase):
    @mock.patch(write_row_path)
    def test_simple(self, write_row):
        generate_cli.callback(
            yaml_file=sample_yaml,
            option={},
            debug_internals=None,
            generate_cci_mapping_file=None,
        )
        assert write_row.mock_calls == [
            mock.call(
                "Account",
                {"id": 1, "name": "Default Company Name", "ShippingCountry": "Canada"},
            )
        ]

    def test_eval_arg(self):
        assert eval_arg("5") == 5
        assert eval_arg("abc") == "abc"

    @mock.patch(write_row_path)
    def test_counts(self, write_row):
        generate_cli.callback(
            yaml_file=sample_yaml,
            target_number=("Account", 2),
            option={},
            debug_internals=None,
            generate_cci_mapping_file=None,
        )
        assert write_row.mock_calls == [
            mock.call(
                "Account",
                {"id": 1, "name": "Default Company Name", "ShippingCountry": "Canada"},
            ),
            mock.call(
                "Account",
                {"id": 2, "name": "Default Company Name", "ShippingCountry": "Canada"},
            ),
        ]

    @mock.patch(write_row_path)
    def test_with_option(self, write_row):
        with self.assertWarns(UserWarning):
            generate_cli.callback(
                yaml_file=sample_yaml,
                option={"xyzzy": "abcd"},
                debug_internals=None,
                generate_cci_mapping_file=None,
            )

    @mock.patch(write_row_path)
    def test_with_bad_dburl(self, write_row):
        with self.assertRaises(Exception):
            generate_cli.callback(
                yaml_file=sample_yaml,
                option={},
                dburl="xyzzy:////foo/bar/baz.com",
                debug_internals=None,
                generate_cci_mapping_file=None,
            )

    @mock.patch(write_row_path)
    def test_with_debug_flags_on(self, write_row):
        generate_cli.callback(
            yaml_file=sample_yaml,
            option={},
            debug_internals=True,
            mapping_file=None,
        )

    @mock.patch(write_row_path)
    def test_exception_with_debug_flags_on(self, write_row):
        with NamedTemporaryFile(suffix=".yml") as t:
            with self.assertRaises(DataGenError):
                generate_cli.callback(
                    yaml_file=bad_sample_yaml,
                    option={},
                    debug_internals=True,
                    generate_cci_mapping_file=t.name,
                )
                assert yaml.safe_load(t.name)

    @mock.patch(write_row_path)
    def test_exception_with_debug_flags_off(self, write_row):
        with NamedTemporaryFile(suffix=".yml") as t:
            with self.assertRaises(ClickException):
                generate_cli.callback(
                    yaml_file=bad_sample_yaml,
                    option={},
                    debug_internals=False,
                    generate_cci_mapping_file=t.name,
                )
                assert yaml.safe_load(t.name)

    def test_json(self):
        with mock.patch(
            "snowfakery.cli.sys.stdout", new=StringIO(),
        ) as fake_out:
            generate_cli.main(
                ["--output-format", "json", str(sample_yaml)], standalone_mode=False
            )
            assert json.loads(fake_out.getvalue()) == [
                {
                    "ShippingCountry": "Canada",
                    "_table": "Account",
                    "id": 1,
                    "name": "Default Company Name",
                }
            ]

    def test_json_output_file(self):
        with TemporaryDirectory() as t:
            generate_cli.main(
                [str(sample_yaml), "--output-file", Path(t) / "foo.json"],
                standalone_mode=False,
            )

    def test_json_output_file_2(self):
        with TemporaryDirectory() as t:
            generate_cli.main(
                [
                    str(sample_yaml),
                    "--output-format",
                    "json",
                    "--output-file",
                    Path(t) / "foo.json",
                ],
                standalone_mode=False,
            )
