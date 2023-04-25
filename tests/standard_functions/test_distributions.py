from unittest import mock
from io import StringIO

import pytest

from snowfakery.data_generator import generate
from snowfakery.data_gen_exceptions import DataGenError

pytest.importorskip("numpy")


class TestStatisticalDistributions:
    def test_random_distribution_normal(self, generated_rows):
        yaml = """
        - plugin: snowfakery.standard_plugins.statistical_distributions.StatisticalDistributions
        - object: A
          fields:
            b:
              StatisticalDistributions.binomial:
                n: 10
                p: 0.3
                seed: 1
        """
        generate(StringIO(yaml), {}, None)
        assert len(generated_rows.mock_calls) == 1
        assert generated_rows.mock_calls == [mock.call("A", {"id": 1, "b": 3})]

    def test_random_distribution_param_errors(self, generated_rows):
        yaml = """
        - plugin: snowfakery.standard_plugins.statistical_distributions.StatisticalDistributions
        - object: A
          fields:
            b:
              StatisticalDistributions.lognormal:
                n: 10
                p: 0.1
                q: 0.2
        """
        with pytest.raises(DataGenError) as e:
            generate(StringIO(yaml), {}, None)
        assert "lognormal" in str(e.value)

    def test_random_distribution_unknown(self, generated_rows):
        yaml = """
        - plugin: snowfakery.standard_plugins.statistical_distributions.StatisticalDistributions
        - object: A
          fields:
            b:
              StatisticalDistributions.bogus:
                n: 10
                p: 0.1
                q: 0.2
        """
        with pytest.raises(DataGenError) as e:
            generate(StringIO(yaml), {}, None)

        assert "StatisticalDistributions" in str(e.value)
        assert "no attribute" in str(e.value)
        assert "bogus" in str(e.value)
