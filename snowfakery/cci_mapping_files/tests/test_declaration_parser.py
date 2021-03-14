from snowfakery.cci_mapping_files.declaration_parser import (
    SObjectRuleDeclaration,
    unify,
)

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
