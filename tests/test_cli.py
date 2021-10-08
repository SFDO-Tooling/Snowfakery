import pytest
from unittest import mock
from pathlib import Path
from tempfile import TemporaryDirectory
from io import StringIO
import json
import re
import sys
from tests.utils import named_temporary_file_path

import yaml
from requests.exceptions import RequestException
from click.exceptions import ClickException, BadParameter

from snowfakery.cli import generate_cli, eval_arg, main, VersionMessage
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
            target_number=(2, "Account"),
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
    def test_counts_backwards(self, write_row):
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
        generate_cli.callback(yaml_file=sample_yaml, option={}, debug_internals=True)

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

    def test_sql_output_file(self):
        with TemporaryDirectory() as t:
            generate_cli.main(
                [str(sample_yaml), "--output-file", Path(t) / "foo.sql"],
                standalone_mode=False,
            )

    def test_from_cli__target_number(self, capsys):
        generate_cli.main(
            [str(sample_yaml), "--target-number", "Account", "5"], standalone_mode=False
        )
        stdout = capsys.readouterr().out

        assert len(re.findall(r"Account\(", stdout)) == 5

    def test_from_cli__reps(self, capsys):
        generate_cli.main([str(sample_yaml), "--reps", "3"], standalone_mode=False)
        stdout = capsys.readouterr().out

        assert len(re.findall(r"Account\(", stdout)) == 3

    def test_from_cli__bad_target_number(self):
        with pytest.raises(BadParameter):
            generate_cli.main(
                [str(sample_yaml), "--target-number", "abc", "def"],
                standalone_mode=False,
            )

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

    def test_from_cli__unknown_format(self, capsys):
        with pytest.raises(ClickException) as e:
            generate_cli.callback(
                yaml_file=str(sample_yaml),
                target_number=("Account", 5),
                output_format="xyzzy",
                output_files=["foo.txt"],
            )
        assert "xyzzy" in str(e.value)
        Path("foo.txt").unlink()

    def test_from_cli__pluggable_output_stream(self):
        with named_temporary_file_path(suffix=".yml") as t:
            generate_cli.main(
                [
                    str(sample_yaml),
                    "--output-format",
                    "examples.YamlOutputStream",
                    "--output-file",
                    t,
                ],
                standalone_mode=False,
            )
            assert t.exists()

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
        _ = sys  # shut up linter
        with pytest.raises(SystemExit), mock.patch("sys.argv", ["snowfakery"]):
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

    def test_output_folder__error(self):
        with TemporaryDirectory() as tempdir, pytest.raises(ClickException):
            generate_cli.main(
                [
                    str(sample_yaml),
                    "--output-folder",
                    tempdir,
                    "--output-format",
                    "json",
                ],
                standalone_mode=False,
            )


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
                        "json",
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

    def test_mutually_exclusive_targets(self):
        with pytest.raises(ClickException) as e:
            generate_cli.main(
                [str(sample_yaml), "--reps", "50", "--target-count", "Account", "100"],
                standalone_mode=False,
            )
        assert "mutually exclusive" in str(e.value)

    def test_cli_errors__cannot_infer_output_format(self):
        with pytest.raises(ClickException, match="No format supplied"):
            with TemporaryDirectory() as t:
                generate_cli.main(
                    [
                        str(sample_yaml),
                        "--output-file",
                        Path(t) / "bob",
                    ],
                    standalone_mode=False,
                )

    def test_version_report__current_version(self, capsys, vcr, snowfakery_rootdir):
        # hand-minimized VCR cassette
        cassette = (
            snowfakery_rootdir
            / "tests/cassettes/ManualEditTestCLIOptionChecking.test_version_report__current_version.yaml"
        )
        assert cassette.exists()

        with pytest.raises(SystemExit), mock.patch(
            "snowfakery.cli.version", "2.0.3"
        ), vcr.use_cassette(str(cassette)):
            generate_cli.main(["--version"])
        captured = capsys.readouterr()
        assert captured.out.startswith("snowfakery")
        assert "Python: 3." in captured.out
        assert "Properly installed" in captured.out
        assert "You have the latest version of Snowfakery" in captured.out

    def test_version_report__old_version(self, capsys, vcr, snowfakery_rootdir):
        # hand-minimized VCR cassette
        cassette = (
            snowfakery_rootdir
            / "tests/cassettes/ManualEditTestCLIOptionChecking.test_version_report__current_version.yaml"
        )
        assert cassette.exists()

        with pytest.raises(SystemExit), mock.patch(
            "snowfakery.cli.version", "1.5"
        ), vcr.use_cassette(str(cassette)):
            generate_cli.main(["--version"])
        captured = capsys.readouterr()
        assert captured.out.startswith("snowfakery")
        assert "Python: 3." in captured.out
        assert "Properly installed" in captured.out
        assert (
            "An update to Snowfakery is available: 2.0.3" in captured.out
        ), captured.out

    def test_version_report__error(self, capsys, vcr, snowfakery_rootdir):
        with pytest.raises(SystemExit), mock.patch(
            "requests.get", side_effect=RequestException
        ):
            generate_cli.main(["--version"])
        captured = capsys.readouterr()
        assert "Error checking snowfakery version:" in captured.out

    def test_version_mod__called(self):
        with pytest.raises(SystemExit), mock.patch.object(
            VersionMessage, "__mod__", wraps=lambda vars: ""
        ) as mod:
            generate_cli.main(["--version"])
        assert len(mod.mock_calls) == 1
