from io import StringIO

import pytest

from snowfakery.api import generate_data
from snowfakery.standard_plugins.UniqueId import as_bool, UniqueId
from snowfakery import data_gen_exceptions as exc
from snowfakery.data_generator_runtime_object_model import StructuredValue
from snowfakery.recipe_validator import ValidationContext


class TestUniqueIdBuiltin:
    def test_simple(self, generated_rows):
        yaml = """
        - object: Example
          count: 2
          fields:
            unique: ${{unique_id}}
        """
        generate_data(StringIO(yaml), plugin_options={"big_ids": "True"})
        assert generated_rows.row_values(0, "unique")
        assert generated_rows.row_values(1, "unique")

    def test_simple_iterations(self, generated_rows):
        yaml = """
        - plugin: snowfakery.standard_plugins.UniqueId
        - object: Example
          count: 2
          fields:
            unique: ${{UniqueId.unique_id}}
        """
        generate_data(
            StringIO(yaml),
            target_number=("Example", 4),
            plugin_options={"big_ids": "False"},
        )
        assert generated_rows.row_values(0, "unique")
        assert generated_rows.row_values(1, "unique")
        assert generated_rows.row_values(2, "unique")
        assert generated_rows.row_values(3, "unique")

    def test_continuations(self, generate_data_with_continuation, generated_rows):
        yaml = """
        - plugin: snowfakery.standard_plugins.UniqueId
        - object: Example
          just_once: True
          fields:
            __uniquifier:
              UniqueId.NumericIdGenerator:
            unique: ${{__uniquifier.unique_id}}
        - object: Example
          count: 2
          fields:
            __uniquifier:
              UniqueId.NumericIdGenerator:
            unique: ${{__uniquifier.unique_id}}
        """
        generate_data_with_continuation(
            yaml=yaml,
            target_number=("Example", 1),
            times=3,
            plugin_options={"big_ids": "False"},
        )
        a = generated_rows.row_values(0, "unique")
        b = generated_rows.row_values(1, "unique")
        c = generated_rows.row_values(2, "unique")
        d = generated_rows.row_values(3, "unique")
        assert all([a, b, c, d])
        assert len(set([a, b, c, d])) == 4


class TestAlphaCodeBuiltiin:
    def test_alpha_code(self, generated_rows):
        yaml = """
        - object: Example
          count: 2
          fields:
            unique: ${{unique_alpha_code}}
        """
        generate_data(StringIO(yaml))
        assert len(generated_rows.row_values(0, "unique")) >= 8
        assert len(generated_rows.row_values(1, "unique")) >= 8

    def test_alpha_code_small_ids(self, generated_rows):
        yaml = """
        - object: Example
          count: 2
          fields:
            unique: ${{unique_alpha_code}}
        """
        generate_data(StringIO(yaml), plugin_options={"big_ids": "False"})
        assert len(generated_rows.row_values(0, "unique")) >= 8
        assert len(generated_rows.row_values(1, "unique")) >= 8


class TestNumericIdGenerator:
    def test_custom_multipart(self, generated_rows):
        yaml = """
        - plugin: snowfakery.standard_plugins.UniqueId
        - var: MyGenerator
          value:
            UniqueId.NumericIdGenerator:
              template: 5, index
        - object: Example
          count: 2
          fields:
            unique: ${{MyGenerator.unique_id}}
        """
        generate_data(StringIO(yaml), plugin_options={"big_ids": "False"})
        assert str(generated_rows.row_values(0, "unique"))
        assert str(generated_rows.row_values(1, "unique"))

    def test_with_pid(self, generated_rows):
        yaml = """
        - plugin: snowfakery.standard_plugins.UniqueId
        - var: MyGenerator
          value:
            UniqueId.NumericIdGenerator:
              template: pid, 5, index
        - object: Example
          count: 2
          fields:
            unique: ${{MyGenerator.unique_id}}
        """
        generate_data(StringIO(yaml))
        assert generated_rows.row_values(0, "unique")

    def test_with_pid_option(self, generated_rows):
        yaml = """
        - plugin: snowfakery.standard_plugins.UniqueId
        - var: MyGenerator
          value:
            UniqueId.NumericIdGenerator:
              template: pid, 9, index
        - object: Example
          count: 2
          fields:
            unique: ${{MyGenerator.unique_id}}
        """
        generate_data(StringIO(yaml), plugin_options={"pid": "3"})
        assert generated_rows.row_values(0, "unique")

    def test_bad_template(self):
        yaml = """
        - plugin: snowfakery.standard_plugins.UniqueId
        - var: MyGenerator
          value:
            UniqueId.NumericIdGenerator:
              template: pid, foo, 9, index
        - object: Example
          count: 2
          fields:
            unique: ${{MyGenerator.unique_id}}
        """
        with pytest.raises(exc.DataGenError) as e:
            generate_data(StringIO(yaml), plugin_options={"pid": "3"})
        assert "foo" in str(e.value)

    def test_bad_template__2(self):
        yaml = """
        - plugin: snowfakery.standard_plugins.UniqueId
        - var: MyGenerator
          value:
            UniqueId.NumericIdGenerator:
              template: pid, 9.7, index
        - object: Example
          count: 2
          fields:
            unique: ${{MyGenerator.unique_id}}
        """
        with pytest.raises(exc.DataGenError) as e:
            generate_data(StringIO(yaml), plugin_options={"pid": "3"})
        assert "9.7" in str(e.value)


class TestAlphaCodeGenerator:
    def test_alpha(self, generated_rows):
        yaml = """
        - plugin: snowfakery.standard_plugins.UniqueId
        - var: MyGenerator
          value:
            UniqueId.AlphaCodeGenerator: pid,index
        - object: Example
          count: 2
          fields:
            unique: ${{MyGenerator.unique_id}}
        """
        generate_data(
            StringIO(yaml),
            plugin_options={"big_ids": "True", "pid": "3333333333333333"},
        )
        assert len(generated_rows.row_values(0, "unique")) > 8
        assert len(generated_rows.row_values(1, "unique")) > 8

    def test_custom_alphabets(self, generated_rows):
        with open("examples/unique_id/alphabet.recipe.yml") as f:
            generate_data(f)
        assert len(generated_rows.row_values(0, "big_alpha_example")) > 6
        assert set(generated_rows.row_values(0, "dna_example")).issubset("ACGT")
        assert set(str(generated_rows.row_values(0, "num_example"))).issubset(
            "0123456789"
        )

    def test_alpha_small(self, generated_rows):
        with open("examples/unique_id/min_length.recipe.yml") as f:
            generate_data(
                f,
                plugin_options={"big_ids": "False"},
            )
        assert len(generated_rows.row_values(0, "unique")) == 6
        assert len(generated_rows.row_values(1, "unique")) == 6

    def test_alpha_small_sequential(self, generated_rows):
        yaml = """
        - plugin: snowfakery.standard_plugins.UniqueId
        - var: MyGenerator
          value:
            UniqueId.AlphaCodeGenerator:
              template: index
              min_chars: 4
              randomize_codes: False
        - object: Example
          count: 10
          fields:
            unique: ${{MyGenerator.unique_id}}
        """
        generate_data(
            StringIO(yaml),
            plugin_options={"big_ids": "True"},
        )
        assert len(generated_rows.row_values(0, "unique")) == 4
        assert len(generated_rows.row_values(1, "unique")) == 4
        assert len(generated_rows.row_values(9, "unique")) == 4

    def test_alpha_small_sequential_with_template(self, generated_rows):
        yaml = """
        - plugin: snowfakery.standard_plugins.UniqueId
        - var: MyGenerator
          value:
            UniqueId.AlphaCodeGenerator:
              template: 3,index
              min_chars: 4
              randomize_codes: False
        - object: Example
          count: 10
          fields:
            unique: ${{MyGenerator.unique_id}}
        """
        generate_data(
            StringIO(yaml),
            plugin_options={"big_ids": "True"},
        )
        assert len(generated_rows.row_values(0, "unique")) == 4
        assert len(generated_rows.row_values(1, "unique")) == 4
        assert len(generated_rows.row_values(9, "unique")) == 4

    def test_alpha_custom_alphabet_min_chars(self, generated_rows):
        yaml = """
        - plugin: snowfakery.standard_plugins.UniqueId
        - var: MyGenerator
          value:
            UniqueId.AlphaCodeGenerator:
              template: 3,index
              min_chars: 1000
              randomize_codes: False
              alphabet: ABC123!
        - object: Example
          count: 1
          fields:
            unique: ${{MyGenerator.unique_id}}
        """
        generate_data(
            StringIO(yaml),
            plugin_options={"big_ids": "True"},
        )
        assert len(generated_rows.row_values(0, "unique")) == 1000
        assert set(generated_rows.row_values(0, "unique")).issubset(set("ABC123!"))

    def test_alpha_custom_alphabet_random(self, generated_rows):
        yaml = """
        - plugin: snowfakery.standard_plugins.UniqueId
        - var: MyGenerator
          value:
            UniqueId.AlphaCodeGenerator:
              template: 9999,index
              min_chars: 20
              randomize_codes: True
              alphabet: ABC123!
        - object: Example
          count: 1
          fields:
            unique: ${{MyGenerator.unique_id}}
        """
        generate_data(
            StringIO(yaml),
            plugin_options={"big_ids": "True"},
        )
        assert len(generated_rows.row_values(0, "unique")) >= 20
        assert set(generated_rows.row_values(0, "unique")).issubset(set("ABC123!"))

    def test_alpha_large_sequential_with_template(self, generated_rows):
        yaml = """
        - plugin: snowfakery.standard_plugins.UniqueId
        - var: MyGenerator
          value:
            UniqueId.AlphaCodeGenerator:
              template: 3,index
              min_chars: 20
              randomize_codes: False
        - object: Example
          count: 10
          fields:
            unique: ${{MyGenerator.unique_id}}
        """
        generate_data(StringIO(yaml), plugin_options={"big_ids": "True"})
        assert len(generated_rows.row_values(0, "unique")) >= 20


class TestAsBool:
    def test_bool_conversions(self):
        assert as_bool("False") is False
        assert as_bool("0") is False
        assert as_bool("no") is False
        assert as_bool(0) is False
        assert as_bool(False) is False
        assert as_bool("True") is True
        assert as_bool("1") is True
        assert as_bool("YES") is True
        assert as_bool(1) is True
        assert as_bool(True) is True
        with pytest.raises(TypeError):
            as_bool("BLAH")
        with pytest.raises(TypeError):
            as_bool(3.145)


class TestNumericIdGeneratorValidator:
    """Test validators for UniqueId.NumericIdGenerator"""

    def test_valid_default_template(self):
        """Test valid call with default template"""
        context = ValidationContext()
        sv = StructuredValue("UniqueId.NumericIdGenerator", {}, "test.yml", 10)

        UniqueId.Validators.validate_NumericIdGenerator(sv, context)

        assert len(context.errors) == 0
        assert len(context.warnings) == 0

    def test_valid_template_with_pid(self):
        """Test valid template with pid, context, index"""
        context = ValidationContext()
        sv = StructuredValue(
            "UniqueId.NumericIdGenerator",
            {"template": "pid,context,index"},
            "test.yml",
            10,
        )

        UniqueId.Validators.validate_NumericIdGenerator(sv, context)

        assert len(context.errors) == 0

    def test_valid_template_with_numeric(self):
        """Test valid template with numeric values"""
        context = ValidationContext()
        sv = StructuredValue(
            "UniqueId.NumericIdGenerator", {"template": "5, index"}, "test.yml", 10
        )

        UniqueId.Validators.validate_NumericIdGenerator(sv, context)

        assert len(context.errors) == 0

    def test_valid_template_positional_arg(self):
        """Test valid template as positional argument"""
        context = ValidationContext()
        sv = StructuredValue(
            "UniqueId.NumericIdGenerator", {"_": "pid,index"}, "test.yml", 10
        )
        sv.args = ["pid,index"]

        UniqueId.Validators.validate_NumericIdGenerator(sv, context)

        assert len(context.errors) == 0

    def test_invalid_template_part(self):
        """Test error for invalid template part"""
        context = ValidationContext()
        sv = StructuredValue(
            "UniqueId.NumericIdGenerator", {"template": "pid,foo,index"}, "test.yml", 10
        )

        UniqueId.Validators.validate_NumericIdGenerator(sv, context)

        assert len(context.errors) >= 1
        assert any(
            "invalid template part 'foo'" in err.message.lower()
            for err in context.errors
        )

    def test_invalid_template_type(self):
        """Test error when template is not a string"""
        context = ValidationContext()
        sv = StructuredValue(
            "UniqueId.NumericIdGenerator", {"template": 123}, "test.yml", 10
        )

        UniqueId.Validators.validate_NumericIdGenerator(sv, context)

        assert len(context.errors) >= 1
        assert any("must be a string" in err.message.lower() for err in context.errors)

    def test_unknown_parameter_warning(self):
        """Test warning for unknown parameters"""
        context = ValidationContext()
        sv = StructuredValue(
            "UniqueId.NumericIdGenerator",
            {"template": "index", "unknown_param": "value"},
            "test.yml",
            10,
        )

        UniqueId.Validators.validate_NumericIdGenerator(sv, context)

        assert len(context.warnings) >= 1
        assert any(
            "unknown parameter" in warn.message.lower() for warn in context.warnings
        )

    def test_valid_parts_combinations(self):
        """Test all valid part combinations"""
        context = ValidationContext()

        # Test all valid parts
        valid_templates = [
            "index",
            "pid",
            "context",
            "pid,index",
            "context,index",
            "pid,context,index",
            "5,index",
            "pid,99,index",
        ]

        for template in valid_templates:
            context = ValidationContext()
            sv = StructuredValue(
                "UniqueId.NumericIdGenerator", {"template": template}, "test.yml", 10
            )

            UniqueId.Validators.validate_NumericIdGenerator(sv, context)

            assert len(context.errors) == 0, f"Template '{template}' should be valid"


class TestAlphaCodeGeneratorValidator:
    """Test validators for UniqueId.AlphaCodeGenerator"""

    def test_valid_default_call(self):
        """Test valid call with default parameters"""
        context = ValidationContext()
        sv = StructuredValue("UniqueId.AlphaCodeGenerator", {}, "test.yml", 10)

        UniqueId.Validators.validate_AlphaCodeGenerator(sv, context)

        assert len(context.errors) == 0
        assert len(context.warnings) == 0

    def test_valid_template(self):
        """Test valid template parameter"""
        context = ValidationContext()
        sv = StructuredValue(
            "UniqueId.AlphaCodeGenerator",
            {"template": "pid,context,index"},
            "test.yml",
            10,
        )

        UniqueId.Validators.validate_AlphaCodeGenerator(sv, context)

        assert len(context.errors) == 0

    def test_invalid_template_part(self):
        """Test error for invalid template part"""
        context = ValidationContext()
        sv = StructuredValue(
            "UniqueId.AlphaCodeGenerator",
            {"template": "invalid,index"},
            "test.yml",
            10,
        )

        UniqueId.Validators.validate_AlphaCodeGenerator(sv, context)

        assert len(context.errors) >= 1
        assert any(
            "invalid template part 'invalid'" in err.message.lower()
            for err in context.errors
        )

    def test_valid_alphabet(self):
        """Test valid alphabet parameter"""
        context = ValidationContext()
        sv = StructuredValue(
            "UniqueId.AlphaCodeGenerator",
            {"alphabet": "ACGT"},
            "test.yml",
            10,
        )

        UniqueId.Validators.validate_AlphaCodeGenerator(sv, context)

        assert len(context.errors) == 0

    def test_alphabet_not_string(self):
        """Test error when alphabet is not a string"""
        context = ValidationContext()
        sv = StructuredValue(
            "UniqueId.AlphaCodeGenerator",
            {"alphabet": 123},
            "test.yml",
            10,
        )

        UniqueId.Validators.validate_AlphaCodeGenerator(sv, context)

        assert len(context.errors) >= 1
        assert any("must be a string" in err.message.lower() for err in context.errors)

    def test_alphabet_too_short(self):
        """Test error when alphabet has less than 2 characters"""
        context = ValidationContext()
        sv = StructuredValue(
            "UniqueId.AlphaCodeGenerator",
            {"alphabet": "A"},
            "test.yml",
            10,
        )

        UniqueId.Validators.validate_AlphaCodeGenerator(sv, context)

        assert len(context.errors) >= 1
        assert any(
            "at least 2 characters" in err.message.lower() for err in context.errors
        )

    def test_valid_min_chars(self):
        """Test valid min_chars parameter"""
        context = ValidationContext()
        sv = StructuredValue(
            "UniqueId.AlphaCodeGenerator",
            {"min_chars": 10},
            "test.yml",
            10,
        )

        UniqueId.Validators.validate_AlphaCodeGenerator(sv, context)

        assert len(context.errors) == 0

    def test_min_chars_not_integer(self):
        """Test error when min_chars is not an integer"""
        context = ValidationContext()
        sv = StructuredValue(
            "UniqueId.AlphaCodeGenerator",
            {"min_chars": "10"},
            "test.yml",
            10,
        )

        UniqueId.Validators.validate_AlphaCodeGenerator(sv, context)

        assert len(context.errors) >= 1
        assert any(
            "must be an integer" in err.message.lower() for err in context.errors
        )

    def test_min_chars_not_positive(self):
        """Test error when min_chars is not positive"""
        context = ValidationContext()
        sv = StructuredValue(
            "UniqueId.AlphaCodeGenerator",
            {"min_chars": 0},
            "test.yml",
            10,
        )

        UniqueId.Validators.validate_AlphaCodeGenerator(sv, context)

        assert len(context.errors) >= 1
        assert any("must be positive" in err.message.lower() for err in context.errors)

    def test_min_chars_negative(self):
        """Test error when min_chars is negative"""
        context = ValidationContext()
        sv = StructuredValue(
            "UniqueId.AlphaCodeGenerator",
            {"min_chars": -5},
            "test.yml",
            10,
        )

        UniqueId.Validators.validate_AlphaCodeGenerator(sv, context)

        assert len(context.errors) >= 1
        assert any("must be positive" in err.message.lower() for err in context.errors)

    def test_valid_randomize_codes(self):
        """Test valid randomize_codes parameter"""
        context = ValidationContext()
        sv = StructuredValue(
            "UniqueId.AlphaCodeGenerator",
            {"randomize_codes": True},
            "test.yml",
            10,
        )

        UniqueId.Validators.validate_AlphaCodeGenerator(sv, context)

        assert len(context.errors) == 0

    def test_randomize_codes_not_boolean(self):
        """Test error when randomize_codes is not a boolean"""
        context = ValidationContext()
        sv = StructuredValue(
            "UniqueId.AlphaCodeGenerator",
            {"randomize_codes": "true"},
            "test.yml",
            10,
        )

        UniqueId.Validators.validate_AlphaCodeGenerator(sv, context)

        assert len(context.errors) >= 1
        assert any("must be a boolean" in err.message.lower() for err in context.errors)

    def test_unknown_parameter_warning(self):
        """Test warning for unknown parameters"""
        context = ValidationContext()
        sv = StructuredValue(
            "UniqueId.AlphaCodeGenerator",
            {"unknown_param": "value"},
            "test.yml",
            10,
        )

        UniqueId.Validators.validate_AlphaCodeGenerator(sv, context)

        assert len(context.warnings) >= 1
        assert any(
            "unknown parameter" in warn.message.lower() for warn in context.warnings
        )

    def test_all_parameters_valid(self):
        """Test all parameters together with valid values"""
        context = ValidationContext()
        sv = StructuredValue(
            "UniqueId.AlphaCodeGenerator",
            {
                "template": "pid,index",
                "alphabet": "ACGT",
                "min_chars": 8,
                "randomize_codes": False,
            },
            "test.yml",
            10,
        )

        UniqueId.Validators.validate_AlphaCodeGenerator(sv, context)

        assert len(context.errors) == 0
        assert len(context.warnings) == 0

    def test_alphabet_too_small_for_randomization(self):
        """Test that small alphabets with randomization are caught"""
        context = ValidationContext()

        # Binary alphabet (2 chars) - too small
        sv = StructuredValue(
            "UniqueId.AlphaCodeGenerator",
            {"alphabet": "01"},
            "test.yml",
            10,
        )
        UniqueId.Validators.validate_AlphaCodeGenerator(sv, context)
        assert len(context.errors) == 1
        assert "too small for randomization" in context.errors[0].message
        assert "at least 6 characters" in context.errors[0].message

        # 3-char alphabet - still too small
        context = ValidationContext()
        sv = StructuredValue(
            "UniqueId.AlphaCodeGenerator",
            {"alphabet": "ABC"},
            "test.yml",
            10,
        )
        UniqueId.Validators.validate_AlphaCodeGenerator(sv, context)
        assert len(context.errors) == 1
        assert "too small for randomization" in context.errors[0].message

    def test_alphabet_small_but_randomization_disabled(self):
        """Test that small alphabets are OK when randomization is disabled"""
        context = ValidationContext()
        sv = StructuredValue(
            "UniqueId.AlphaCodeGenerator",
            {"alphabet": "01", "randomize_codes": False},
            "test.yml",
            10,
        )
        UniqueId.Validators.validate_AlphaCodeGenerator(sv, context)
        # Should only warn about minimum 2 chars, not about randomization
        assert len(context.errors) == 0


class TestUniqueIdJinjaExecution:
    """Test UniqueId plugin functions called directly from Jinja templates"""

    def test_jinja_numeric_id_generator_inline(self):
        """Test calling NumericIdGenerator inline in Jinja"""
        yaml = """
        - plugin: snowfakery.standard_plugins.UniqueId
        - object: Example
          count: 3
          fields:
            id1: ${{UniqueId.NumericIdGenerator(template="index").unique_id}}
            id2: ${{UniqueId.NumericIdGenerator(template="pid,index").unique_id}}
        """
        result = generate_data(StringIO(yaml), validate_only=True)
        assert result.errors == []

    def test_jinja_alpha_code_generator_inline(self):
        """Test calling AlphaCodeGenerator inline in Jinja"""
        yaml = """
        - plugin: snowfakery.standard_plugins.UniqueId
        - object: Example
          count: 2
          fields:
            code1: ${{UniqueId.AlphaCodeGenerator().unique_id}}
            code2: ${{UniqueId.AlphaCodeGenerator(alphabet="ACGT", min_chars=6).unique_id}}
        """
        result = generate_data(StringIO(yaml), validate_only=True)
        assert result.errors == []

    def test_jinja_unique_id_property(self):
        """Test accessing unique_id property directly"""
        yaml = """
        - plugin: snowfakery.standard_plugins.UniqueId
        - object: Example
          fields:
            id: ${{UniqueId.unique_id}}
        """
        result = generate_data(StringIO(yaml), validate_only=True)
        assert result.errors == []

    def test_jinja_with_invalid_template(self):
        """Test Jinja call with invalid template parameter"""
        yaml = """
        - plugin: snowfakery.standard_plugins.UniqueId
        - object: Example
          fields:
            id: ${{UniqueId.NumericIdGenerator(template="invalid_part").unique_id}}
        """
        with pytest.raises(exc.DataGenValidationError) as e:
            generate_data(StringIO(yaml), validate_only=True)
        assert "invalid_part" in str(e.value).lower()


class TestUniqueIdVariableReferencing:
    """Test UniqueId generators stored in variables and referenced later"""

    def test_variable_with_empty_params(self):
        """Test variable holding generator with no parameters"""
        yaml = """
        - plugin: snowfakery.standard_plugins.UniqueId
        - var: gen1
          value:
            UniqueId.NumericIdGenerator:
        - object: Example
          count: 2
          fields:
            test_id: ${{gen1.unique_id}}
        """
        result = generate_data(StringIO(yaml), validate_only=True)
        assert result.errors == []

    def test_variable_with_explicit_none(self):
        """Test variable holding generator with explicit null parameter"""
        yaml = """
        - plugin: snowfakery.standard_plugins.UniqueId
        - var: gen1
          value:
            UniqueId.NumericIdGenerator:
              template: null
        - object: Example
          fields:
            test_id: ${{gen1.unique_id}}
        """
        result = generate_data(StringIO(yaml), validate_only=True)
        assert result.errors == []

    def test_variable_with_positional_arg(self):
        """Test variable holding generator with positional argument"""
        yaml = """
        - plugin: snowfakery.standard_plugins.UniqueId
        - var: gen1
          value:
            UniqueId.NumericIdGenerator: index
        - object: Example
          fields:
            test_id: ${{gen1.unique_id}}
        """
        result = generate_data(StringIO(yaml), validate_only=True)
        assert result.errors == []

    def test_variable_with_keyword_args(self):
        """Test variable holding generator with keyword arguments"""
        yaml = """
        - plugin: snowfakery.standard_plugins.UniqueId
        - var: gen1
          value:
            UniqueId.NumericIdGenerator:
              template: "pid,index"
        - object: Example
          fields:
            test_id: ${{gen1.unique_id}}
        """
        result = generate_data(StringIO(yaml), validate_only=True)
        assert result.errors == []

    def test_alpha_generator_in_variable(self):
        """Test AlphaCodeGenerator stored in variable"""
        yaml = """
        - plugin: snowfakery.standard_plugins.UniqueId
        - var: code_gen
          value:
            UniqueId.AlphaCodeGenerator:
              alphabet: "0123456789ABCDEF"
              min_chars: 8
        - object: Example
          fields:
            code: ${{code_gen.unique_id}}
        """
        result = generate_data(StringIO(yaml), validate_only=True)
        assert result.errors == []

    def test_multiple_generators_in_variables(self):
        """Test multiple generators stored in different variables"""
        yaml = """
        - plugin: snowfakery.standard_plugins.UniqueId
        - var: gen1
          value:
            UniqueId.NumericIdGenerator: index
        - var: gen2
          value:
            UniqueId.NumericIdGenerator: pid,index
        - var: alpha_gen
          value:
            UniqueId.AlphaCodeGenerator:
              alphabet: ACGT
        - object: Example
          fields:
            id1: ${{gen1.unique_id}}
            id2: ${{gen2.unique_id}}
            code: ${{alpha_gen.unique_id}}
        """
        result = generate_data(StringIO(yaml), validate_only=True)
        assert result.errors == []

    def test_variable_with_invalid_alphabet_size(self):
        """Test that invalid alphabet size is caught in variables"""
        yaml = """
        - plugin: snowfakery.standard_plugins.UniqueId
        - var: bad_gen
          value:
            UniqueId.AlphaCodeGenerator:
              alphabet: "01"
        - object: Example
          fields:
            code: ${{bad_gen.unique_id}}
        """
        with pytest.raises(exc.DataGenValidationError) as e:
            generate_data(StringIO(yaml), validate_only=True)
        assert "too small for randomization" in str(e.value)
