import math
from io import StringIO

from snowfakery.api import generate_data
from snowfakery.data_generator_runtime_object_model import StructuredValue
from snowfakery.recipe_validator import ValidationContext
from snowfakery.standard_plugins._math import Math


class TestMathFunctions:
    """Test Math plugin runtime functionality."""

    def test_sqrt_basic(self, generated_rows):
        """Test basic sqrt function"""
        yaml = """
            - plugin: snowfakery.standard_plugins.Math
            - object: Example
              fields:
                result:
                  Math.sqrt: 16
        """
        generate_data(StringIO(yaml))
        result = generated_rows.row_values(0, "result")
        assert result == math.sqrt(16)
        assert result == 4.0

    def test_pow_function(self, generated_rows):
        """Test pow function with Jinja"""
        yaml = """
            - plugin: snowfakery.standard_plugins.Math
            - object: Example
              fields:
                result: ${{Math.pow(2, 10)}}
        """
        generate_data(StringIO(yaml))
        result = generated_rows.row_values(0, "result")
        assert result == math.pow(2, 10)
        assert result == 1024.0

    def test_math_constants(self, generated_rows):
        """Test math constants (pi, e, tau)"""
        yaml = """
            - plugin: snowfakery.standard_plugins.Math
            - object: Example
              fields:
                pi: ${{Math.pi}}
                e: ${{Math.e}}
                tau: ${{Math.tau}}
        """
        generate_data(StringIO(yaml))
        pi_val = generated_rows.row_values(0, "pi")
        e_val = generated_rows.row_values(0, "e")
        tau_val = generated_rows.row_values(0, "tau")

        assert pi_val == math.pi
        assert e_val == math.e
        assert tau_val == math.tau

    def test_round_min_max(self, generated_rows):
        """Test Python builtins: round, min, max"""
        yaml = """
            - plugin: snowfakery.standard_plugins.Math
            - object: Example
              fields:
                rounded: ${{Math.round(3.14159, 2)}}
                minimum: ${{Math.min(10, 20, 5)}}
                maximum: ${{Math.max(10, 20, 5)}}
        """
        generate_data(StringIO(yaml))
        rounded = generated_rows.row_values(0, "rounded")
        minimum = generated_rows.row_values(0, "minimum")
        maximum = generated_rows.row_values(0, "maximum")

        assert rounded == round(3.14159, 2)
        assert rounded == 3.14
        assert minimum == 5
        assert maximum == 20

    def test_trigonometric_functions(self, generated_rows):
        """Test trigonometric functions"""
        yaml = """
            - plugin: snowfakery.standard_plugins.Math
            - object: Example
              fields:
                sine: ${{Math.sin(Math.pi / 2)}}
                cosine: ${{Math.cos(0)}}
                tangent: ${{Math.tan(0)}}
        """
        generate_data(StringIO(yaml))
        sine = generated_rows.row_values(0, "sine")
        cosine = generated_rows.row_values(0, "cosine")
        tangent = generated_rows.row_values(0, "tangent")

        assert abs(sine - 1.0) < 0.0001  # sin(π/2) = 1
        assert cosine == 1.0  # cos(0) = 1
        assert tangent == 0.0  # tan(0) = 0

    def test_ceil_floor(self, generated_rows):
        """Test ceil and floor functions"""
        yaml = """
            - plugin: snowfakery.standard_plugins.Math
            - object: Example
              fields:
                ceiling: ${{Math.ceil(3.2)}}
                floor: ${{Math.floor(3.8)}}
        """
        generate_data(StringIO(yaml))
        ceiling = generated_rows.row_values(0, "ceiling")
        floor_val = generated_rows.row_values(0, "floor")

        assert ceiling == 4
        assert floor_val == 3


class TestMathValidator:
    """Test validators for Math plugin functions."""

    def test_typo_in_function_name(self):
        """Test typo in function name with suggestion"""
        context = ValidationContext()
        sv = StructuredValue("Math.squrt", [16], "test.yml", 10)

        # Call the internal validator directly to test typo detection
        Math.Validators._validate_math_function(sv, context, "squrt")

        assert len(context.errors) >= 1
        assert any(
            "unknown function or constant" in err.message.lower()
            and "sqrt" in err.message.lower()  # Should suggest "sqrt"
            for err in context.errors
        )

    def test_case_sensitivity(self):
        """Test case-sensitive constant names (PI vs pi)"""
        context = ValidationContext()
        sv = StructuredValue("Math.PI", [], "test.yml", 10)

        Math.Validators._validate_math_function(sv, context, "PI")

        assert len(context.errors) >= 1
        assert any(
            "unknown function or constant" in err.message.lower()
            for err in context.errors
        )

    def test_non_existent_function(self):
        """Test completely non-existent function"""
        context = ValidationContext()
        sv = StructuredValue("Math.square_root", [25], "test.yml", 10)

        Math.Validators._validate_math_function(sv, context, "square_root")

        assert len(context.errors) >= 1
        assert any(
            "unknown function or constant" in err.message.lower()
            for err in context.errors
        )

    def test_valid_function_names_no_error(self):
        """Test that valid function names don't produce errors"""
        context = ValidationContext()

        # Test several valid functions
        valid_funcs = ["sqrt", "pow", "sin", "cos", "pi", "e", "round", "min", "max"]

        for func_name in valid_funcs:
            sv = StructuredValue(f"Math.{func_name}", [], "test.yml", 10)
            Math.Validators._validate_math_function(sv, context, func_name)

        # Should have no errors for any valid function
        assert len(context.errors) == 0

    def test_all_validators_created(self):
        """Test that validators are created for all math functions (but not constants)"""
        # Check that common functions have validators
        assert hasattr(Math.Validators, "validate_sqrt")
        assert hasattr(Math.Validators, "validate_pow")
        assert hasattr(Math.Validators, "validate_sin")
        assert hasattr(Math.Validators, "validate_cos")
        assert hasattr(Math.Validators, "validate_round")
        assert hasattr(Math.Validators, "validate_min")
        assert hasattr(Math.Validators, "validate_max")

        # Check that constants do NOT have validators (they're not callable)
        assert not hasattr(Math.Validators, "validate_pi")
        assert not hasattr(Math.Validators, "validate_e")
        assert not hasattr(Math.Validators, "validate_tau")
        assert not hasattr(Math.Validators, "validate_inf")
        assert not hasattr(Math.Validators, "validate_nan")

        # Check that the count is reasonable (50+ callable functions, excluding constants)
        validator_methods = [
            attr for attr in dir(Math.Validators) if attr.startswith("validate_")
        ]
        assert len(validator_methods) >= 45  # Math module has 45+ callable functions

    def test_valid_names_initialized(self):
        """Test that valid_names is initialized at class level"""
        # Should be initialized without needing to instantiate
        assert Math.Validators._valid_names is not None
        assert len(Math.Validators._valid_names) >= 50
        assert "sqrt" in Math.Validators._valid_names
        assert "pi" in Math.Validators._valid_names
        assert "round" in Math.Validators._valid_names
        assert "min" in Math.Validators._valid_names
        assert "max" in Math.Validators._valid_names
