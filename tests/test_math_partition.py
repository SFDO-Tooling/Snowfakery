import pytest
from random import randint
from io import StringIO
from snowfakery import generate_data
from snowfakery.data_gen_exceptions import DataGenError

REPS = 1
SEEDS = [randint(0, 2 ** 32) for r in range(REPS)]


@pytest.mark.parametrize("seed", SEEDS)
class TestMathPartition:
    def test_example(self, generated_rows, seed):
        generate_data(
            "examples/math_partition/math_partition_simple.recipe.yml", seed=seed
        )
        parents = generated_rows.table_values("ParentObject__c")
        children = generated_rows.table_values("ChildObject__c")
        assert sum(p["TotalAmount__c"] for p in parents) == sum(
            c["Amount__c"] for c in children
        ), (parents, children)

    regression_seeds = [824956277]

    @pytest.mark.parametrize("seed2", regression_seeds + SEEDS)
    def test_example_pennies(self, generated_rows, seed, seed2):
        generate_data("examples/math_partition/sum_pennies.recipe.yml", seed=seed2)
        objs = generated_rows.table_values("Values")
        assert round(sum(p["Amount"] for p in objs)) == 100, sum(
            p["Amount"] for p in objs
        )

    @pytest.mark.parametrize("step", [0.01, 0.5, 0.1, 0.20, 0.25, 0.50])
    def test_example_pennies_param(self, generated_rows, seed, step: int):
        generate_data(
            "examples/math_partition/sum_pennies_param.recipe.yml",
            user_options={"step": step},
            seed=seed,
        )
        objs = generated_rows.table_values("Values")
        assert round(sum(p["Amount"] for p in objs)) == 100, sum(
            p["Amount"] for p in objs
        )

    def test_step(self, generated_rows, seed):
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
        generate_data(StringIO(yaml), seed=seed)
        values = generated_rows.table_values("Obj")
        assert 1 <= len(values) <= 6
        amounts = [r["Amount"] for r in values]
        assert sum(amounts) == 60, amounts
        assert sum([r % 10 for r in amounts]) == 0, amounts

    def test_min(self, generated_rows, seed):
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
        generate_data(StringIO(yaml), seed=seed)
        values = generated_rows.table_values("Obj")
        results = [r["Amount"] for r in values]
        assert sum(results) == 60, results
        assert not [r for r in results if r < 5], results

    def test_min_not_factor_of_total(self, generated_rows, seed):
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
        generate_data(StringIO(yaml), seed=seed)
        values = generated_rows.table_values("Obj")
        results = [r["Amount"] for r in values]
        assert sum(results) == 63
        assert not [r for r in results if r < 5], results

    def test_step_not_factor_of_total(self, generated_rows, seed):
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
        generate_data(StringIO(yaml), seed=seed)
        values = generated_rows.table_values("Obj")
        results = [r["Amount"] for r in values]
        assert sum(results) == 63, results
        assert len([r for r in results if r < 5]) <= 1, results

    def test_max(self, generated_rows, seed):
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
        generate_data(StringIO(yaml), seed=seed)
        values = generated_rows.table_values("Obj")
        results = [r["Amount"] for r in values]
        assert sum(results) == 28, results
        assert not [r for r in results if r % 2], results
        assert not [r for r in results if r > 6], results

    def test_bad_step(self, generated_rows, seed):
        yaml = """
    - plugin: snowfakery.standard_plugins.Math
    - object: Obj
      for_each:
        var: child_value
        value:
          Math.random_partition:
            total: 28
            step: 0.3
      fields:
        Amount: ${{child_value}}
        """
        with pytest.raises(DataGenError, match="step.*0.3"):
            generate_data(StringIO(yaml), seed=seed)

    def test_inconsistent_constraints(self, generated_rows, seed):
        yaml = """
    - plugin: snowfakery.standard_plugins.Math
    - object: Obj
      for_each:
        var: child_value
        value:
          Math.random_partition:
            total: 10
            min: 8
            max: 8
            step: 5
      fields:
        Amount: ${{child_value}}
        """
        with pytest.raises(DataGenError, match="constraints"):
            generate_data(StringIO(yaml), seed=seed)
