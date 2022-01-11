from tempfile import TemporaryDirectory
from pathlib import Path
import yaml
from unittest import mock
from io import StringIO

import pytest

from snowfakery import generate_data
from snowfakery.data_generator_runtime import IdManager
from snowfakery.api import SnowfakeryApplication
from snowfakery import data_gen_exceptions as exc


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
        with TemporaryDirectory() as t, mock.patch("warnings.warn") as w:
            outfile = Path(t) / "foo.txt"
            continuation = Path(t) / "out.yml"
            generate_data(
                yaml_file="tests/BDI_generator.yml",
                user_options={"num_accounts": "15"},
                target_number=(20, "Account"),
                debug_internals=True,
                output_format="json",
                output_file=outfile,
                generate_continuation_file=continuation,
            )
            assert outfile.exists()
            assert continuation.exists()
            with continuation.open() as f:
                assert yaml.safe_load(f)
            w.assert_called_once()

    def test_continuation_as_open_file(self):
        with TemporaryDirectory() as t:
            outfile = Path(t) / "foo.json"
            continuation = Path(t) / "cont.yml"
            mapping_file = Path(t) / "mapping.yml"
            with open(continuation, "w") as cont, open(mapping_file, "w") as mapf:
                generate_data(
                    yaml_file="examples/company.yml",
                    target_number=(20, "Employee"),
                    debug_internals=False,
                    output_file=outfile,
                    generate_continuation_file=cont,
                    generate_cci_mapping_file=mapf,
                )
            assert outfile.exists()
            assert continuation.exists()
            with continuation.open() as f:
                assert yaml.safe_load(f)
            assert mapping_file.exists()
            with mapping_file.open() as f:
                assert yaml.safe_load(f)

    def test_parent_application__echo(self):
        called = False

        class MyEmbedder(SnowfakeryApplication):
            def echo(self, *args, **kwargs):
                nonlocal called
                called = True

        meth = "snowfakery.output_streams.DebugOutputStream.close"
        with mock.patch(meth) as close:
            close.side_effect = AssertionError
            generate_data(
                yaml_file="examples/company.yml", parent_application=MyEmbedder()
            )
            assert called

    def test_parent_application__early_finish(self, generated_rows):
        class MyEmbedder(SnowfakeryApplication):
            count = 0

            def check_if_finished(self, idmanager):
                assert isinstance(idmanager, IdManager)
                self.__class__.count += 1
                assert self.__class__.count < 100, "Runaway recipe!"
                return idmanager["Employee"] >= 10

        meth = "snowfakery.output_streams.DebugOutputStream.close"
        with mock.patch(meth) as close:
            close.side_effect = AssertionError
            generate_data(
                yaml_file="examples/company.yml", parent_application=MyEmbedder()
            )
            # called 5 times, after generating 2 employees each
            assert MyEmbedder.count == 5

    def test_embedding__cannot_infer_output_format(self):
        with pytest.raises(exc.DataGenError, match="No format"):
            generate_data(
                yaml_file=StringIO("- object: Foo"),
                output_file=StringIO(),
            )

    def test_parent_application__streams_instead_of_files(self, generated_rows):
        yaml_file = StringIO("""- object: Foo""")
        generate_cci_mapping_file = StringIO()
        output_file = StringIO()
        output_files = [StringIO(), StringIO()]
        continuation_file = StringIO(
            """
        id_manager:
           last_used_ids:
             Foo: 6
        intertable_dependencies: []
        nicknames_and_tables:
           Foo: Foo
        persistent_nicknames: {}
        persistent_objects_by_table: {}
        today: 2021-04-07"""
        )
        generate_continuation_file = StringIO()
        decls = """[{"sf_object": Opportunity, "api": bulk}]"""
        load_declarations = [StringIO(decls), StringIO(decls)]

        generate_data(
            yaml_file=yaml_file,
            generate_cci_mapping_file=generate_cci_mapping_file,
            output_file=output_file,
            output_files=output_files,
            output_format="txt",
            continuation_file=continuation_file,
            generate_continuation_file=generate_continuation_file,
            load_declarations=load_declarations,
        )
        assert generated_rows.table_values("Foo", 0)["id"] == 7
