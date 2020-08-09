import pytest
from unittest import mock
from pathlib import Path
from tempfile import TemporaryDirectory
from io import StringIO
import json
import re
from tests.utils import named_temporary_file_path

import yaml
from click.exceptions import ClickException

from snowfakery.cli import generate_cli, eval_arg, main
from snowfakery.data_gen_exceptions import DataGenError

sample_yaml = Path(__file__).parent / "include_parent.yml"
bad_sample_yaml = Path(__file__).parent / "include_bad_parent.yml"
sample_accounts_yaml = Path(__file__).parent / "gen_sf_standard_objects.yml"

write_row_path = "snowfakery.output_streams.DebugOutputStream.write_single_row"


class TestGenerateFromCLI:
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
        with pytest.warns(UserWarning):
            generate_cli.callback(
                yaml_file=sample_yaml,
                option={"xyzzy": "abcd"},
                debug_internals=None,
                generate_cci_mapping_file=None,
            )

    @mock.patch(write_row_path)
    def test_with_bad_dburl(self, write_row):
        with pytest.raises(Exception):
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
            yaml_file=sample_yaml, option={}, debug_internals=True, mapping_file=None
        )

    @mock.patch(write_row_path)
    def test_exception_with_debug_flags_on(self, write_row):
        with named_temporary_file_path(suffix=".yml") as t:
            with pytest.raises(DataGenError):
                generate_cli.callback(
                    yaml_file=bad_sample_yaml,
                    option={},
                    debug_internals=True,
                    generate_cci_mapping_file=t,
                )
                assert yaml.safe_load(t)

    @mock.patch(write_row_path)
    def test_exception_with_debug_flags_off(self, write_row):
        with named_temporary_file_path(suffix=".yml") as t:
            with pytest.raises(ClickException):
                generate_cli.callback(
                    yaml_file=bad_sample_yaml,
                    option={},
                    debug_internals=False,
                    generate_cci_mapping_file=t,
                )
                assert yaml.safe_load(t)

    def test_json(self):
        with mock.patch("snowfakery.cli.sys.stdout", new=StringIO()) as fake_out:
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

    def test_from_cli__target_number(self, capsys):
        generate_cli.main(
            [str(sample_yaml), "--target-number", "Account", "5"], standalone_mode=False
        )
        stdout = capsys.readouterr().out

        assert len(re.findall(r"Account\(", stdout)) == 5

    def test_from_cli__explicit_format_txt(self, capsys):
        with named_temporary_file_path() as t:
            generate_cli.main(
                [
                    str(sample_yaml),
                    "--target-number",
                    "Account",
                    "5",
                    "--output-format",
                    "txt",
                    "--output-file",
                    str(t),
                ],
                standalone_mode=False,
            )
            with t.open() as f:
                output = f.read()
            assert len(re.findall(r"Account\(", output)) == 5

    def test_from_cli__continuation(self, capsys):
        with TemporaryDirectory() as t:
            mapping_file_path = Path(t) / "mapping.yml"
            database_path = f"{t}/foo.db"
            database_url = f"sqlite:///{database_path}"
            continuation_file = Path(t) / "continuation.yml"
            assert not mapping_file_path.exists()
            generate_cli.main(
                [
                    str(sample_yaml),
                    "--generate-cci-mapping-file",
                    mapping_file_path,
                    "--dburl",
                    database_url,
                    "--generate-continuation-file",
                    continuation_file,
                ],
                standalone_mode=False,
            )
            assert mapping_file_path.exists()
            Path(database_path).unlink()
            generate_cli.main(
                [
                    str(sample_yaml),
                    "--cci-mapping-file",
                    mapping_file_path,
                    "--dburl",
                    database_url,
                    "--continuation-file",
                    continuation_file,
                ],
                standalone_mode=False,
            )

    def test_from_cli__checks_tables_are_empty(self, capsys):
        with TemporaryDirectory() as t:
            mapping_file_path = Path(t) / "mapping.yml"
            database_path = f"{t}/foo.db"
            database_url = f"sqlite:///{database_path}"
            continuation_file = Path(t) / "continuation.yml"
            assert not mapping_file_path.exists()
            generate_cli.main(
                [
                    str(sample_yaml),
                    "--generate-cci-mapping-file",
                    mapping_file_path,
                    "--dburl",
                    database_url,
                    "--generate-continuation-file",
                    continuation_file,
                ],
                standalone_mode=False,
            )
            assert mapping_file_path.exists()
            with pytest.raises(ClickException) as e:
                generate_cli.main(
                    [
                        str(sample_yaml),
                        "--cci-mapping-file",
                        mapping_file_path,
                        "--dburl",
                        database_url,
                        "--continuation-file",
                        continuation_file,
                    ],
                    standalone_mode=False,
                )
                assert "Table already exists" in str(e.value)

    def test_image_outputs(self):
        pytest.importorskip("pygraphviz")
        with TemporaryDirectory() as t:
            png = Path(t) / "out.png"
            svg = Path(t) / "out.svg"
            txt = Path(t) / "out.txt"
            generate_cli.main(
                [
                    str(sample_yaml),
                    "--output-file",
                    png,
                    "--output-file",
                    svg,
                    "--output-file",
                    txt,
                ],
                standalone_mode=False,
            )
            assert png.exists()
            assert svg.exists()
            assert txt.exists()

    def test_cli_errors__mutex(self):
        with pytest.raises(ClickException) as e:
            generate_cli.main(
                [
                    str(sample_yaml),
                    "--dburl",
                    "sqlite:////tmp/foo.db",
                    "--output-file",
                    "/tmp/foo.svg",
                ],
                standalone_mode=False,
            )
        assert "output-file" in str(e.value)

    def test_cli_errors__mutex2(self):
        with pytest.raises(ClickException) as e:
            generate_cli.main(
                [
                    str(sample_yaml),
                    "--dburl",
                    "sqlite:////tmp/foo.db",
                    "--output-format",
                    "svg",
                ],
                standalone_mode=False,
            )
        assert "output-format" in str(e.value)

    def test_cli_errors__mutex3(self):
        with named_temporary_file_path() as tempfile:
            with open(tempfile, "w") as t:
                t.write("")

            with pytest.raises(ClickException) as e:
                generate_cli.main(
                    [str(sample_yaml), "--cci-mapping-file", tempfile],
                    standalone_mode=False,
                )
            assert "--cci-mapping-file" in str(e.value)

    def test_module_main(self, capsys):
        with pytest.raises(SystemExit):
            main()

        assert "Usage:" in capsys.readouterr().err

    def test_output_folder(self):
        with TemporaryDirectory() as tempdir:
            generate_cli.main(
                [
                    str(sample_yaml),
                    "--output-folder",
                    tempdir,
                    "--output-file",
                    "foo.json",
                ],
                standalone_mode=False,
            )
            assert isinstance(json.load(Path(tempdir, "foo.json").open()), list)

    def test_output_folder__csv(self):
        with TemporaryDirectory() as tempdir:
            generate_cli.main(
                [
                    str(sample_yaml),
                    "--output-folder",
                    tempdir,
                    "--output-format",
                    "csv",
                ],
                standalone_mode=False,
            )
            assert Path(tempdir, "Account.csv").exists()

    def test_output_folder__csv_new_folder(self):
        with TemporaryDirectory() as tempdir:
            generate_cli.main(
                [
                    str(sample_yaml),
                    "--output-folder",
                    Path(tempdir, "foo"),
                    "--output-format",
                    "csv",
                ],
                standalone_mode=False,
            )
            assert Path(tempdir, "foo", "Account.csv").exists()


class TestCLIOptionChecking:
    def test_mapping_file_no_dburl(self):
        with pytest.raises(ClickException):
            generate_cli.main(
                ["--mapping_file", str(str(sample_yaml)), str(sample_yaml)],
                standalone_mode=False,
            )

    def test_mutually_exclusive(self):
        with pytest.raises(ClickException) as e:
            with TemporaryDirectory() as t:
                generate_cli.main(
                    [
                        str(sample_yaml),
                        "--dburl",
                        f"sqlite:///{t}/foo.db",
                        "--output-format",
                        "JSON",
                    ],
                    standalone_mode=False,
                )
        assert "mutually exclusive" in str(e.value)

        with pytest.raises(ClickException) as e:
            generate_cli.main(
                [
                    str(sample_yaml),
                    "--cci-mapping-file",
                    str(sample_yaml),
                    "--output-format",
                    "JSON",
                ],
                standalone_mode=False,
            )
        assert "apping-file" in str(e.value)
