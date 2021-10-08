from pathlib import Path
from io import StringIO

from snowfakery.cci_mapping_files.declaration_parser import (
    SObjectRuleDeclaration,
    SObjectRuleDeclarationFile,
    unify,
)
from snowfakery.cli import generate_cli

import yaml

declarations = [
    SObjectRuleDeclaration(sf_object="foo", priority="low", api="rest"),
    SObjectRuleDeclaration(sf_object="foo", priority="high", api="buLK"),
    SObjectRuleDeclaration(sf_object="foo", priority="low", api="sMart"),
    SObjectRuleDeclaration(sf_object="foo", priority="high", bulk_mode="serial"),
    SObjectRuleDeclaration(sf_object="foo", priority="low", bulk_mode="parallel"),
    SObjectRuleDeclaration(sf_object="bar", priority="medium", api="rest"),
    SObjectRuleDeclaration(sf_object="bar", priority="low", api="bulk"),
    SObjectRuleDeclaration(sf_object="bar", priority="medium", api="smart"),
    SObjectRuleDeclaration(sf_object="bar", priority="medium", bulk_mode="serial"),
    SObjectRuleDeclaration(sf_object="bar", priority="high", bulk_mode="Parallel"),
    SObjectRuleDeclaration(sf_object="foo", priority="low", batch_size=2000),
    SObjectRuleDeclaration(sf_object="foo", priority="low", anchor_date="2000-01-01"),
]


class TestDeclarationParser:
    def test_priority_overrides(self):
        unification = unify(declarations)
        assert unification == {
            "bar": SObjectRuleDeclaration(
                sf_object="bar",
                load_after=None,
                priority=None,
                api="rest",
                batch_size=None,
                bulk_mode="parallel",
                anchor_date=None,
            ),
            "foo": SObjectRuleDeclaration(
                sf_object="foo",
                load_after=None,
                priority=None,
                api="bulk",
                batch_size=2000,
                bulk_mode="serial",
                anchor_date="2000-01-01",
            ),
        }

    def test_load_after_appending(self):
        declarations = [
            SObjectRuleDeclaration(sf_object="foo", priority="low", load_after="A"),
            SObjectRuleDeclaration(sf_object="foo", priority="high", load_after="B"),
            SObjectRuleDeclaration(sf_object="foo", priority="medium", load_after="C"),
            SObjectRuleDeclaration(sf_object="bar", priority="low", load_after="D"),
            SObjectRuleDeclaration(sf_object="bar", priority="high", load_after="E"),
            SObjectRuleDeclaration(sf_object="bar", priority="high", load_after="A"),
        ]
        unification = unify(declarations)
        assert set(unification["foo"].load_after) == set(["A", "B", "C"])
        assert set(unification["bar"].load_after) == set(["A", "D", "E"])

    def test_cli__infers_load_file(self, tmpdir):
        sample_yaml = Path(__file__).parent / "mapping_mixins.recipe.yml"
        mapping_yaml = Path(tmpdir) / "mapping.yml"
        generate_cli.main(
            [str(sample_yaml), "--generate-cci-mapping-file", str(mapping_yaml)],
            standalone_mode=False,
        )
        map_data = yaml.safe_load(mapping_yaml.read_text())
        assert list(map_data.keys()) == [
            "Insert Account",
            "Insert Contact",
            "Insert Opportunity",
        ]
        assert map_data["Insert Account"]["api"] == "rest"

    def test_cli__explicit_file(self, tmpdir):
        sample_yaml = Path(__file__).parent / "mapping_mixins.recipe.yml"
        load_yaml = Path(__file__).parent / "mapping_mixins-reverse.load.yml"
        mapping_yaml = Path(tmpdir) / "mapping.yml"
        generate_cli.main(
            [
                str(sample_yaml),
                "--generate-cci-mapping-file",
                str(mapping_yaml),
                "--load-declarations",
                str(load_yaml),
            ],
            standalone_mode=False,
        )
        map_data = yaml.safe_load(mapping_yaml.read_text())
        assert list(map_data.keys()) == [
            "Insert Contact",
            "Insert Opportunity",
            "Insert Account",
        ]
        assert map_data["Insert Opportunity"]["bulk_mode"] == "serial"

    def test_cli__file_no_dots(self, tmpdir):
        sample_yaml = Path(__file__).parent / "no_extension_filename"
        mapping_yaml = Path(tmpdir) / "mapping.yml"
        generate_cli.main(
            [
                str(sample_yaml),
                "--generate-cci-mapping-file",
                str(mapping_yaml),
            ],
            standalone_mode=False,
        )
        map_data = yaml.safe_load(mapping_yaml.read_text())
        assert list(map_data.keys()) == [
            "Insert foo",
        ]

    def test_cli__multiple_files(self, tmpdir):
        sample_yaml = Path(__file__).parent / "mapping_mixins.recipe.yml"
        load_yaml = Path(__file__).parent / "mapping_mixins.load.yml"
        override_yaml = Path(__file__).parent / "mapping_mixins-override.load.yml"
        mapping_yaml = Path(tmpdir) / "mapping.yml"
        generate_cli.main(
            [
                str(sample_yaml),
                "--generate-cci-mapping-file",
                str(mapping_yaml),
                "--load-declarations",
                str(load_yaml),
                "--load-declarations",
                str(override_yaml),
            ],
            standalone_mode=False,
        )
        map_data = yaml.safe_load(mapping_yaml.read_text())
        assert list(map_data.keys()) == [
            "Insert Account",
            "Insert Contact",
            "Insert Opportunity",
        ]
        assert map_data["Insert Account"]["api"] == "rest"
        assert map_data["Insert Contact"]["api"] == "rest"
        assert map_data["Insert Opportunity"]["api"] == "bulk"

    def test_circular_references__force_order(self, generate_in_tmpdir):
        circular_test = (Path(__file__).parent / "circular_references.yml").read_text()
        print(generate_in_tmpdir)
        with generate_in_tmpdir(
            circular_test, load_declarations=["tests/cci/mapping_mixins.load.yml"]
        ) as (mapping, connection):
            assert tuple(mapping.keys()) == tuple(
                ["Insert Account", "Insert Contact", "Insert Opportunity"]
            )

    def test_parse_from_open_file(self):
        s = StringIO(
            """
         - sf_object: Foo
           api: bulk
        """
        )
        SObjectRuleDeclarationFile.parse_from_yaml(s)

    def test_parse_from_path(self):
        sample_yaml = Path(__file__).parent / "mapping_mixins-override.load.yml"
        SObjectRuleDeclarationFile.parse_from_yaml(sample_yaml)
