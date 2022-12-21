import pytest
from io import StringIO
from snowfakery import generate_data

REPS = 1


@pytest.mark.parametrize("_", range(REPS))
class TestSummation:
    def test_example(self, generated_rows, _):
        generate_data("examples/math_partition_simple.recipe.yml")
        parents = generated_rows.table_values("ParentObject__c")
        children = generated_rows.table_values("ChildObject__c")
        assert sum(p["TotalAmount__c"] for p in parents) == sum(
            c["Amount__c"] for c in children
        ), (parents, children)

    def test_example_pennies(self, generated_rows, _):
        generate_data("examples/sum_pennies.yml")
        objs = generated_rows.table_values("Values")
        assert round(sum(p["Amount"] for p in objs)) == 100, sum(
            p["Amount"] for p in objs
        )

    @pytest.mark.parametrize("step", [0.01, 0.5, 0.1, 0.20, 0.25, 0.50])
    def test_example_pennies_param(self, generated_rows, _, step: int):
        generate_data("examples/sum_pennies_param.yml", user_options={"step": step})
        objs = generated_rows.table_values("Values")
        assert round(sum(p["Amount"] for p in objs)) == 100, sum(
            p["Amount"] for p in objs
        )

    def test_step(self, generated_rows, _):
        yaml = """
    - plugin: snowfakery.standard_plugins.Math
    - object: Obj
      for_each:
        var: child_value
        value:
          Math.random_partition:
            total: 60
            step: 10
      fields:
        Amount: ${{child_value}}
        """
        generate_data(StringIO(yaml))
        values = generated_rows.table_values("Obj")
        assert 1 <= len(values) <= 6
        amounts = [r["Amount"] for r in values]
        assert sum(amounts) == 60, amounts
        assert sum([r % 10 for r in amounts]) == 0, amounts

    def test_min(self, generated_rows, _):
        yaml = """
    - plugin: snowfakery.standard_plugins.Math
    - object: Obj
      for_each:
        var: child_value
        value:
          Math.random_partition:
            total: 60
            min: 5
      fields:
        Amount: ${{child_value}}
        """
        generate_data(StringIO(yaml))
        values = generated_rows.table_values("Obj")
        results = [r["Amount"] for r in values]
        assert sum(results) == 60, results
        assert not [r for r in results if r < 5], results

    def test_min_not_factor_of_total(self, generated_rows, _):
        yaml = """
    - plugin: snowfakery.standard_plugins.Math
    - object: Obj
      for_each:
        var: child_value
        value:
          Math.random_partition:
            total: 63
            min: 5
      fields:
        Amount: ${{child_value}}
        """
        generate_data(StringIO(yaml))
        values = generated_rows.table_values("Obj")
        results = [r["Amount"] for r in values]
        assert sum(results) == 63
        assert not [r for r in results if r < 5], results

    def test_step_not_factor_of_total(self, generated_rows, _):
        yaml = """
    - plugin: snowfakery.standard_plugins.Math
    - object: Obj
      for_each:
        var: child_value
        value:
          Math.random_partition:
            total: 63
            step: 5
      fields:
        Amount: ${{child_value}}
        """
        generate_data(StringIO(yaml))
        values = generated_rows.table_values("Obj")
        results = [r["Amount"] for r in values]
        assert sum(results) == 63, results
        assert len([r for r in results if r < 5]) <= 1, results

    def test_max(self, generated_rows, _):
        yaml = """
    - plugin: snowfakery.standard_plugins.Math
    - object: Obj
      for_each:
        var: child_value
        value:
          Math.random_partition:
            total: 28
            step: 2
            max: 6
      fields:
        Amount: ${{child_value}}
        """
        generate_data(StringIO(yaml))
        values = generated_rows.table_values("Obj")
        results = [r["Amount"] for r in values]
        assert sum(results) == 28, results
        assert not [r for r in results if r % 2], results
        assert not [r for r in results if r > 6], results
