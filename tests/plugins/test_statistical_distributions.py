"""Unit tests for StatisticalDistributions plugin validators."""

from io import StringIO

import pytest

pytest.importorskip("numpy")

from snowfakery.api import generate_data
from snowfakery import data_gen_exceptions as exc
from snowfakery.data_generator_runtime_object_model import StructuredValue
from snowfakery.recipe_validator import ValidationContext
from snowfakery.standard_plugins.statistical_distributions import (
    StatisticalDistributions,
)


class TestNormalValidator:
    """Test validators for StatisticalDistributions.normal()"""

    def test_valid_default(self):
        """Test valid call with default parameters"""
        context = ValidationContext()
        sv = StructuredValue("StatisticalDistributions.normal", {}, "test.yml", 10)

        StatisticalDistributions.Validators.validate_normal(sv, context)

        assert len(context.errors) == 0
        assert len(context.warnings) == 0

    def test_valid_custom_params(self):
        """Test valid call with custom loc and scale"""
        context = ValidationContext()
        sv = StructuredValue(
            "StatisticalDistributions.normal",
            {"loc": 100, "scale": 15},
            "test.yml",
            10,
        )

        StatisticalDistributions.Validators.validate_normal(sv, context)

        assert len(context.errors) == 0

    def test_valid_with_seed(self):
        """Test valid call with seed parameter"""
        context = ValidationContext()
        sv = StructuredValue(
            "StatisticalDistributions.normal",
            {"loc": 0, "scale": 1, "seed": 42},
            "test.yml",
            10,
        )

        StatisticalDistributions.Validators.validate_normal(sv, context)

        assert len(context.errors) == 0

    def test_invalid_scale_negative(self):
        """Test error when scale is negative"""
        context = ValidationContext()
        sv = StructuredValue(
            "StatisticalDistributions.normal", {"scale": -5}, "test.yml", 10
        )

        StatisticalDistributions.Validators.validate_normal(sv, context)

        assert len(context.errors) >= 1
        assert any(
            "scale" in err.message.lower() and "positive" in err.message.lower()
            for err in context.errors
        )

    def test_invalid_scale_zero(self):
        """Test error when scale is zero"""
        context = ValidationContext()
        sv = StructuredValue(
            "StatisticalDistributions.normal", {"scale": 0}, "test.yml", 10
        )

        StatisticalDistributions.Validators.validate_normal(sv, context)

        assert len(context.errors) >= 1
        assert any(
            "scale" in err.message.lower() and "positive" in err.message.lower()
            for err in context.errors
        )

    def test_invalid_seed_type(self):
        """Test error when seed is not an integer"""
        context = ValidationContext()
        sv = StructuredValue(
            "StatisticalDistributions.normal", {"seed": "42"}, "test.yml", 10
        )

        StatisticalDistributions.Validators.validate_normal(sv, context)

        assert len(context.errors) >= 1
        assert any(
            "seed" in err.message.lower() and "integer" in err.message.lower()
            for err in context.errors
        )

    def test_unknown_parameter_warning(self):
        """Test warning for unknown parameters"""
        context = ValidationContext()
        sv = StructuredValue(
            "StatisticalDistributions.normal",
            {"loc": 0, "unknown_param": "value"},
            "test.yml",
            10,
        )

        StatisticalDistributions.Validators.validate_normal(sv, context)

        assert len(context.warnings) >= 1
        assert any(
            "unknown parameter" in warn.message.lower() for warn in context.warnings
        )

    def test_jinja_normal_valid(self):
        """Test normal() called inline in Jinja template"""
        yaml = """
        - plugin: snowfakery.standard_plugins.statistical_distributions.StatisticalDistributions
        - object: Example
          fields:
            value1: ${{StatisticalDistributions.normal()}}
            value2: ${{StatisticalDistributions.normal(loc=100, scale=15)}}
        """
        result = generate_data(StringIO(yaml), validate_only=True)
        assert result.errors == []

    def test_jinja_normal_invalid(self):
        """Test normal() with invalid scale in Jinja"""
        yaml = """
        - plugin: snowfakery.standard_plugins.statistical_distributions.StatisticalDistributions
        - object: Example
          fields:
            value: ${{StatisticalDistributions.normal(scale=-5)}}
        """
        with pytest.raises(exc.DataGenValidationError) as e:
            generate_data(StringIO(yaml), validate_only=True)
        # Can be either our validation error or numpy's runtime error
        assert "scale" in str(e.value).lower()


class TestLognormalValidator:
    """Test validators for StatisticalDistributions.lognormal()"""

    def test_valid_default(self):
        """Test valid call with default parameters"""
        context = ValidationContext()
        sv = StructuredValue("StatisticalDistributions.lognormal", {}, "test.yml", 10)

        StatisticalDistributions.Validators.validate_lognormal(sv, context)

        assert len(context.errors) == 0

    def test_valid_custom_params(self):
        """Test valid call with custom mean and sigma"""
        context = ValidationContext()
        sv = StructuredValue(
            "StatisticalDistributions.lognormal",
            {"mean": 0.5, "sigma": 2.0},
            "test.yml",
            10,
        )

        StatisticalDistributions.Validators.validate_lognormal(sv, context)

        assert len(context.errors) == 0

    def test_invalid_sigma_negative(self):
        """Test error when sigma is negative"""
        context = ValidationContext()
        sv = StructuredValue(
            "StatisticalDistributions.lognormal", {"sigma": -1}, "test.yml", 10
        )

        StatisticalDistributions.Validators.validate_lognormal(sv, context)

        assert len(context.errors) >= 1
        assert any(
            "sigma" in err.message.lower() and "positive" in err.message.lower()
            for err in context.errors
        )

    def test_invalid_sigma_zero(self):
        """Test error when sigma is zero"""
        context = ValidationContext()
        sv = StructuredValue(
            "StatisticalDistributions.lognormal", {"sigma": 0}, "test.yml", 10
        )

        StatisticalDistributions.Validators.validate_lognormal(sv, context)

        assert len(context.errors) >= 1
        assert any(
            "sigma" in err.message.lower() and "positive" in err.message.lower()
            for err in context.errors
        )

    def test_invalid_seed(self):
        """Test error when seed is not integer"""
        context = ValidationContext()
        sv = StructuredValue(
            "StatisticalDistributions.lognormal", {"seed": 3.14}, "test.yml", 10
        )

        StatisticalDistributions.Validators.validate_lognormal(sv, context)

        assert len(context.errors) >= 1
        assert any("seed" in err.message.lower() for err in context.errors)

    def test_unknown_params(self):
        """Test warning for unknown parameters"""
        context = ValidationContext()
        sv = StructuredValue(
            "StatisticalDistributions.lognormal",
            {"mean": 0, "bad_param": 1},
            "test.yml",
            10,
        )

        StatisticalDistributions.Validators.validate_lognormal(sv, context)

        assert len(context.warnings) >= 1

    def test_jinja_lognormal_valid(self):
        """Test lognormal() called inline in Jinja template"""
        yaml = """
        - plugin: snowfakery.standard_plugins.statistical_distributions.StatisticalDistributions
        - object: Example
          fields:
            value1: ${{StatisticalDistributions.lognormal()}}
            value2: ${{StatisticalDistributions.lognormal(mean=0.5, sigma=2.0)}}
        """
        result = generate_data(StringIO(yaml), validate_only=True)
        assert result.errors == []

    def test_jinja_lognormal_invalid(self):
        """Test lognormal() with invalid sigma in Jinja"""
        yaml = """
        - plugin: snowfakery.standard_plugins.statistical_distributions.StatisticalDistributions
        - object: Example
          fields:
            value: ${{StatisticalDistributions.lognormal(sigma=-1)}}
        """
        with pytest.raises(exc.DataGenValidationError) as e:
            generate_data(StringIO(yaml), validate_only=True)
        assert "sigma" in str(e.value).lower()


class TestBinomialValidator:
    """Test validators for StatisticalDistributions.binomial()"""

    def test_valid_required_params(self):
        """Test valid call with required parameters"""
        context = ValidationContext()
        sv = StructuredValue(
            "StatisticalDistributions.binomial", {"n": 10, "p": 0.5}, "test.yml", 10
        )

        StatisticalDistributions.Validators.validate_binomial(sv, context)

        assert len(context.errors) == 0

    def test_valid_with_seed(self):
        """Test valid call with seed"""
        context = ValidationContext()
        sv = StructuredValue(
            "StatisticalDistributions.binomial",
            {"n": 100, "p": 0.3, "seed": 42},
            "test.yml",
            10,
        )

        StatisticalDistributions.Validators.validate_binomial(sv, context)

        assert len(context.errors) == 0

    def test_missing_n(self):
        """Test error when n is missing"""
        context = ValidationContext()
        sv = StructuredValue(
            "StatisticalDistributions.binomial", {"p": 0.5}, "test.yml", 10
        )

        StatisticalDistributions.Validators.validate_binomial(sv, context)

        assert len(context.errors) >= 1
        assert any(
            "missing" in err.message.lower() and "n" in err.message.lower()
            for err in context.errors
        )

    def test_missing_p(self):
        """Test error when p is missing"""
        context = ValidationContext()
        sv = StructuredValue(
            "StatisticalDistributions.binomial", {"n": 10}, "test.yml", 10
        )

        StatisticalDistributions.Validators.validate_binomial(sv, context)

        assert len(context.errors) >= 1
        assert any(
            "missing" in err.message.lower() and "p" in err.message.lower()
            for err in context.errors
        )

    def test_n_not_integer(self):
        """Test error when n is not an integer"""
        context = ValidationContext()
        sv = StructuredValue(
            "StatisticalDistributions.binomial", {"n": 10.5, "p": 0.5}, "test.yml", 10
        )

        StatisticalDistributions.Validators.validate_binomial(sv, context)

        assert len(context.errors) >= 1
        assert any(
            "n" in err.message.lower() and "integer" in err.message.lower()
            for err in context.errors
        )

    def test_n_not_positive(self):
        """Test error when n is not positive"""
        context = ValidationContext()
        sv = StructuredValue(
            "StatisticalDistributions.binomial", {"n": 0, "p": 0.5}, "test.yml", 10
        )

        StatisticalDistributions.Validators.validate_binomial(sv, context)

        assert len(context.errors) >= 1
        assert any(
            "n" in err.message.lower() and "positive" in err.message.lower()
            for err in context.errors
        )

    def test_p_negative(self):
        """Test error when p is negative"""
        context = ValidationContext()
        sv = StructuredValue(
            "StatisticalDistributions.binomial", {"n": 10, "p": -0.5}, "test.yml", 10
        )

        StatisticalDistributions.Validators.validate_binomial(sv, context)

        assert len(context.errors) >= 1
        assert any(
            "p" in err.message.lower() and "between" in err.message.lower()
            for err in context.errors
        )

    def test_p_greater_than_one(self):
        """Test error when p is greater than 1"""
        context = ValidationContext()
        sv = StructuredValue(
            "StatisticalDistributions.binomial", {"n": 10, "p": 1.5}, "test.yml", 10
        )

        StatisticalDistributions.Validators.validate_binomial(sv, context)

        assert len(context.errors) >= 1
        assert any(
            "p" in err.message.lower() and "between" in err.message.lower()
            for err in context.errors
        )

    def test_unknown_params(self):
        """Test warning for unknown parameters"""
        context = ValidationContext()
        sv = StructuredValue(
            "StatisticalDistributions.binomial",
            {"n": 10, "p": 0.5, "unknown": 1},
            "test.yml",
            10,
        )

        StatisticalDistributions.Validators.validate_binomial(sv, context)

        assert len(context.warnings) >= 1

    def test_jinja_binomial_valid(self):
        """Test binomial() called inline in Jinja template"""
        yaml = """
        - plugin: snowfakery.standard_plugins.statistical_distributions.StatisticalDistributions
        - object: Example
          fields:
            value1: ${{StatisticalDistributions.binomial(n=10, p=0.5)}}
            value2: ${{StatisticalDistributions.binomial(n=100, p=0.3, seed=42)}}
        """
        result = generate_data(StringIO(yaml), validate_only=True)
        assert result.errors == []

    def test_jinja_binomial_invalid(self):
        """Test binomial() with missing parameters in Jinja"""
        yaml = """
        - plugin: snowfakery.standard_plugins.statistical_distributions.StatisticalDistributions
        - object: Example
          fields:
            value: ${{StatisticalDistributions.binomial(n=10)}}
        """
        with pytest.raises(exc.DataGenValidationError) as e:
            generate_data(StringIO(yaml), validate_only=True)
        assert "missing" in str(e.value).lower() and "p" in str(e.value).lower()


class TestExponentialValidator:
    """Test validators for StatisticalDistributions.exponential()"""

    def test_valid_default(self):
        """Test valid call with default parameters"""
        context = ValidationContext()
        sv = StructuredValue("StatisticalDistributions.exponential", {}, "test.yml", 10)

        StatisticalDistributions.Validators.validate_exponential(sv, context)

        assert len(context.errors) == 0

    def test_valid_custom_scale(self):
        """Test valid call with custom scale"""
        context = ValidationContext()
        sv = StructuredValue(
            "StatisticalDistributions.exponential", {"scale": 2.5}, "test.yml", 10
        )

        StatisticalDistributions.Validators.validate_exponential(sv, context)

        assert len(context.errors) == 0

    def test_invalid_scale_negative(self):
        """Test error when scale is negative"""
        context = ValidationContext()
        sv = StructuredValue(
            "StatisticalDistributions.exponential", {"scale": -1}, "test.yml", 10
        )

        StatisticalDistributions.Validators.validate_exponential(sv, context)

        assert len(context.errors) >= 1
        assert any(
            "scale" in err.message.lower() and "positive" in err.message.lower()
            for err in context.errors
        )

    def test_invalid_scale_zero(self):
        """Test error when scale is zero"""
        context = ValidationContext()
        sv = StructuredValue(
            "StatisticalDistributions.exponential", {"scale": 0}, "test.yml", 10
        )

        StatisticalDistributions.Validators.validate_exponential(sv, context)

        assert len(context.errors) >= 1
        assert any(
            "scale" in err.message.lower() and "positive" in err.message.lower()
            for err in context.errors
        )

    def test_invalid_seed(self):
        """Test error when seed is not integer"""
        context = ValidationContext()
        sv = StructuredValue(
            "StatisticalDistributions.exponential", {"seed": "42"}, "test.yml", 10
        )

        StatisticalDistributions.Validators.validate_exponential(sv, context)

        assert len(context.errors) >= 1
        assert any("seed" in err.message.lower() for err in context.errors)

    def test_unknown_params(self):
        """Test warning for unknown parameters"""
        context = ValidationContext()
        sv = StructuredValue(
            "StatisticalDistributions.exponential",
            {"scale": 1, "bad": 1},
            "test.yml",
            10,
        )

        StatisticalDistributions.Validators.validate_exponential(sv, context)

        assert len(context.warnings) >= 1

    def test_jinja_exponential_valid(self):
        """Test exponential() called inline in Jinja template"""
        yaml = """
        - plugin: snowfakery.standard_plugins.statistical_distributions.StatisticalDistributions
        - object: Example
          fields:
            value1: ${{StatisticalDistributions.exponential()}}
            value2: ${{StatisticalDistributions.exponential(scale=2.5)}}
        """
        result = generate_data(StringIO(yaml), validate_only=True)
        assert result.errors == []

    def test_jinja_exponential_invalid(self):
        """Test exponential() with invalid scale in Jinja"""
        yaml = """
        - plugin: snowfakery.standard_plugins.statistical_distributions.StatisticalDistributions
        - object: Example
          fields:
            value: ${{StatisticalDistributions.exponential(scale=-1)}}
        """
        with pytest.raises(exc.DataGenValidationError) as e:
            generate_data(StringIO(yaml), validate_only=True)
        assert "scale" in str(e.value).lower()


class TestPoissonValidator:
    """Test validators for StatisticalDistributions.poisson()"""

    def test_valid_required_param(self):
        """Test valid call with required lam parameter"""
        context = ValidationContext()
        sv = StructuredValue(
            "StatisticalDistributions.poisson", {"lam": 5.0}, "test.yml", 10
        )

        StatisticalDistributions.Validators.validate_poisson(sv, context)

        assert len(context.errors) == 0

    def test_valid_with_seed(self):
        """Test valid call with seed"""
        context = ValidationContext()
        sv = StructuredValue(
            "StatisticalDistributions.poisson", {"lam": 5.0, "seed": 42}, "test.yml", 10
        )

        StatisticalDistributions.Validators.validate_poisson(sv, context)

        assert len(context.errors) == 0

    def test_missing_lam(self):
        """Test error when lam is missing"""
        context = ValidationContext()
        sv = StructuredValue("StatisticalDistributions.poisson", {}, "test.yml", 10)

        StatisticalDistributions.Validators.validate_poisson(sv, context)

        assert len(context.errors) >= 1
        assert any(
            "missing" in err.message.lower() and "lam" in err.message.lower()
            for err in context.errors
        )

    def test_lam_not_numeric(self):
        """Test error when lam is not numeric"""
        context = ValidationContext()
        sv = StructuredValue(
            "StatisticalDistributions.poisson", {"lam": "five"}, "test.yml", 10
        )

        StatisticalDistributions.Validators.validate_poisson(sv, context)

        assert len(context.errors) >= 1
        assert any(
            "lam" in err.message.lower() and "numeric" in err.message.lower()
            for err in context.errors
        )

    def test_lam_not_positive(self):
        """Test error when lam is not positive"""
        context = ValidationContext()
        sv = StructuredValue(
            "StatisticalDistributions.poisson", {"lam": -1}, "test.yml", 10
        )

        StatisticalDistributions.Validators.validate_poisson(sv, context)

        assert len(context.errors) >= 1
        assert any(
            "lam" in err.message.lower() and "positive" in err.message.lower()
            for err in context.errors
        )

    def test_lam_zero(self):
        """Test error when lam is zero"""
        context = ValidationContext()
        sv = StructuredValue(
            "StatisticalDistributions.poisson", {"lam": 0}, "test.yml", 10
        )

        StatisticalDistributions.Validators.validate_poisson(sv, context)

        assert len(context.errors) >= 1
        assert any(
            "lam" in err.message.lower() and "positive" in err.message.lower()
            for err in context.errors
        )

    def test_unknown_params(self):
        """Test warning for unknown parameters"""
        context = ValidationContext()
        sv = StructuredValue(
            "StatisticalDistributions.poisson",
            {"lam": 5, "unknown": 1},
            "test.yml",
            10,
        )

        StatisticalDistributions.Validators.validate_poisson(sv, context)

        assert len(context.warnings) >= 1

    def test_jinja_poisson_valid(self):
        """Test poisson() called inline in Jinja template"""
        yaml = """
        - plugin: snowfakery.standard_plugins.statistical_distributions.StatisticalDistributions
        - object: Example
          fields:
            value1: ${{StatisticalDistributions.poisson(lam=5.0)}}
            value2: ${{StatisticalDistributions.poisson(lam=10, seed=42)}}
        """
        result = generate_data(StringIO(yaml), validate_only=True)
        assert result.errors == []

    def test_jinja_poisson_invalid(self):
        """Test poisson() with missing lam in Jinja"""
        yaml = """
        - plugin: snowfakery.standard_plugins.statistical_distributions.StatisticalDistributions
        - object: Example
          fields:
            value: ${{StatisticalDistributions.poisson()}}
        """
        with pytest.raises(exc.DataGenValidationError) as e:
            generate_data(StringIO(yaml), validate_only=True)
        assert "missing" in str(e.value).lower() and "lam" in str(e.value).lower()


class TestGammaValidator:
    """Test validators for StatisticalDistributions.gamma()"""

    def test_valid_required_params(self):
        """Test valid call with required parameters"""
        context = ValidationContext()
        sv = StructuredValue(
            "StatisticalDistributions.gamma",
            {"shape": 2.0, "scale": 1.0},
            "test.yml",
            10,
        )

        StatisticalDistributions.Validators.validate_gamma(sv, context)

        assert len(context.errors) == 0

    def test_valid_with_seed(self):
        """Test valid call with seed"""
        context = ValidationContext()
        sv = StructuredValue(
            "StatisticalDistributions.gamma",
            {"shape": 2.0, "scale": 1.0, "seed": 42},
            "test.yml",
            10,
        )

        StatisticalDistributions.Validators.validate_gamma(sv, context)

        assert len(context.errors) == 0

    def test_missing_shape(self):
        """Test error when shape is missing"""
        context = ValidationContext()
        sv = StructuredValue(
            "StatisticalDistributions.gamma", {"scale": 1.0}, "test.yml", 10
        )

        StatisticalDistributions.Validators.validate_gamma(sv, context)

        assert len(context.errors) >= 1
        assert any(
            "missing" in err.message.lower() and "shape" in err.message.lower()
            for err in context.errors
        )

    def test_missing_scale(self):
        """Test error when scale is missing"""
        context = ValidationContext()
        sv = StructuredValue(
            "StatisticalDistributions.gamma", {"shape": 2.0}, "test.yml", 10
        )

        StatisticalDistributions.Validators.validate_gamma(sv, context)

        assert len(context.errors) >= 1
        assert any(
            "missing" in err.message.lower() and "scale" in err.message.lower()
            for err in context.errors
        )

    def test_shape_not_positive(self):
        """Test error when shape is not positive"""
        context = ValidationContext()
        sv = StructuredValue(
            "StatisticalDistributions.gamma",
            {"shape": 0, "scale": 1.0},
            "test.yml",
            10,
        )

        StatisticalDistributions.Validators.validate_gamma(sv, context)

        assert len(context.errors) >= 1
        assert any(
            "shape" in err.message.lower() and "positive" in err.message.lower()
            for err in context.errors
        )

    def test_shape_negative(self):
        """Test error when shape is negative"""
        context = ValidationContext()
        sv = StructuredValue(
            "StatisticalDistributions.gamma",
            {"shape": -1, "scale": 1.0},
            "test.yml",
            10,
        )

        StatisticalDistributions.Validators.validate_gamma(sv, context)

        assert len(context.errors) >= 1
        assert any(
            "shape" in err.message.lower() and "positive" in err.message.lower()
            for err in context.errors
        )

    def test_scale_not_positive(self):
        """Test error when scale is not positive"""
        context = ValidationContext()
        sv = StructuredValue(
            "StatisticalDistributions.gamma",
            {"shape": 2.0, "scale": 0},
            "test.yml",
            10,
        )

        StatisticalDistributions.Validators.validate_gamma(sv, context)

        assert len(context.errors) >= 1
        assert any(
            "scale" in err.message.lower() and "positive" in err.message.lower()
            for err in context.errors
        )

    def test_scale_negative(self):
        """Test error when scale is negative"""
        context = ValidationContext()
        sv = StructuredValue(
            "StatisticalDistributions.gamma",
            {"shape": 2.0, "scale": -1},
            "test.yml",
            10,
        )

        StatisticalDistributions.Validators.validate_gamma(sv, context)

        assert len(context.errors) >= 1
        assert any(
            "scale" in err.message.lower() and "positive" in err.message.lower()
            for err in context.errors
        )

    def test_unknown_params(self):
        """Test warning for unknown parameters"""
        context = ValidationContext()
        sv = StructuredValue(
            "StatisticalDistributions.gamma",
            {"shape": 2.0, "scale": 1.0, "unknown": 1},
            "test.yml",
            10,
        )

        StatisticalDistributions.Validators.validate_gamma(sv, context)

        assert len(context.warnings) >= 1

    def test_jinja_gamma_valid(self):
        """Test gamma() called inline in Jinja template"""
        yaml = """
        - plugin: snowfakery.standard_plugins.statistical_distributions.StatisticalDistributions
        - object: Example
          fields:
            value1: ${{StatisticalDistributions.gamma(shape=2.0, scale=1.0)}}
            value2: ${{StatisticalDistributions.gamma(shape=3.0, scale=2.0, seed=42)}}
        """
        result = generate_data(StringIO(yaml), validate_only=True)
        assert result.errors == []

    def test_jinja_gamma_invalid(self):
        """Test gamma() with missing parameters in Jinja"""
        yaml = """
        - plugin: snowfakery.standard_plugins.statistical_distributions.StatisticalDistributions
        - object: Example
          fields:
            value: ${{StatisticalDistributions.gamma(shape=2.0)}}
        """
        with pytest.raises(exc.DataGenValidationError) as e:
            generate_data(StringIO(yaml), validate_only=True)
        assert "missing" in str(e.value).lower() and "scale" in str(e.value).lower()


class TestStatisticalDistributionsIntegration:
    """Integration tests for StatisticalDistributions with Jinja and variables"""

    def test_all_distributions_jinja_valid(self):
        """Test all distributions called inline in Jinja"""
        yaml = """
        - plugin: snowfakery.standard_plugins.statistical_distributions.StatisticalDistributions
        - object: Example
          fields:
            normal: ${{StatisticalDistributions.normal()}}
            lognormal: ${{StatisticalDistributions.lognormal()}}
            binomial: ${{StatisticalDistributions.binomial(n=10, p=0.5)}}
            exponential: ${{StatisticalDistributions.exponential()}}
            poisson: ${{StatisticalDistributions.poisson(lam=5)}}
            gamma: ${{StatisticalDistributions.gamma(shape=2, scale=1)}}
        """
        result = generate_data(StringIO(yaml), validate_only=True)
        assert result.errors == []

    def test_distributions_in_variables(self):
        """Test distributions stored in variables"""
        yaml = """
        - plugin: snowfakery.standard_plugins.statistical_distributions.StatisticalDistributions
        - var: norm_val
          value:
            StatisticalDistributions.normal:
              loc: 100
              scale: 15
        - var: binom_val
          value:
            StatisticalDistributions.binomial:
              n: 10
              p: 0.3
        - object: Example
          fields:
            value1: ${{norm_val}}
            value2: ${{binom_val}}
        """
        result = generate_data(StringIO(yaml), validate_only=True)
        assert result.errors == []

    def test_nested_function_calls(self):
        """Test distributions with nested function arguments"""
        yaml = """
        - plugin: snowfakery.standard_plugins.statistical_distributions.StatisticalDistributions
        - object: Example
          fields:
            # Using random_number for scale
            value: ${{StatisticalDistributions.normal(loc=0, scale=random_number(min=1, max=5))}}
        """
        result = generate_data(StringIO(yaml), validate_only=True)
        assert result.errors == []

    def test_error_propagation_jinja(self):
        """Test that validation errors in Jinja are caught"""
        yaml = """
        - plugin: snowfakery.standard_plugins.statistical_distributions.StatisticalDistributions
        - object: Example
          fields:
            # Multiple errors: missing parameters
            bad1: ${{StatisticalDistributions.binomial(n=10)}}
            bad2: ${{StatisticalDistributions.gamma(shape=2)}}
        """
        with pytest.raises(exc.DataGenValidationError) as e:
            generate_data(StringIO(yaml), validate_only=True)
        # Should catch both errors
        assert "missing" in str(e.value).lower()

    def test_all_distributions_with_seed(self):
        """Test all distributions with seed parameter"""
        yaml = """
        - plugin: snowfakery.standard_plugins.statistical_distributions.StatisticalDistributions
        - object: Example
          fields:
            normal: ${{StatisticalDistributions.normal(seed=1)}}
            lognormal: ${{StatisticalDistributions.lognormal(seed=2)}}
            binomial: ${{StatisticalDistributions.binomial(n=10, p=0.5, seed=3)}}
            exponential: ${{StatisticalDistributions.exponential(seed=4)}}
            poisson: ${{StatisticalDistributions.poisson(lam=5, seed=5)}}
            gamma: ${{StatisticalDistributions.gamma(shape=2, scale=1, seed=6)}}
        """
        result = generate_data(StringIO(yaml), validate_only=True)
        assert result.errors == []

    def test_mixed_structured_and_jinja(self):
        """Test mixing StructuredValue and Jinja calls"""
        yaml = """
        - plugin: snowfakery.standard_plugins.statistical_distributions.StatisticalDistributions
        - var: dist_var
          value:
            StatisticalDistributions.normal:
              loc: 50
              scale: 10
        - object: Example
          fields:
            # StructuredValue in field
            structured_field:
              StatisticalDistributions.binomial:
                n: 10
                p: 0.3
            # Jinja call
            jinja_field: ${{StatisticalDistributions.poisson(lam=5)}}
            # Variable reference
            var_field: ${{dist_var}}
        """
        result = generate_data(StringIO(yaml), validate_only=True)
        assert result.errors == []

    def test_invalid_seed_multiple_distributions(self):
        """Test invalid seed is caught across multiple distributions"""
        yaml = """
        - plugin: snowfakery.standard_plugins.statistical_distributions.StatisticalDistributions
        - object: Example
          fields:
            bad1: ${{StatisticalDistributions.normal(seed="not_an_int")}}
            bad2: ${{StatisticalDistributions.poisson(lam=5, seed=3.14)}}
        """
        with pytest.raises(exc.DataGenValidationError) as e:
            generate_data(StringIO(yaml), validate_only=True)
        assert "seed" in str(e.value).lower() and "integer" in str(e.value).lower()
