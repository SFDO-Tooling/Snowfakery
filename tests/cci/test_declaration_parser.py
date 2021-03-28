from pathlib import Path

from snowfakery.cci_mapping_files.declaration_parser import (
    SObjectRuleDeclaration,
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
                batch_size=None,
                bulk_mode="serial",
                anchor_date=None,
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
        assert map_data["Insert Account"]["api"] == "smart"

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
