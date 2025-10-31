from unittest import mock
from io import StringIO

import pytest

from snowfakery.data_generator import merge_options, generate
from snowfakery.data_gen_exceptions import DataGenNameError, DataGenError
from snowfakery.data_generator_runtime import StoppingCriteria
from snowfakery import data_gen_exceptions as exc


class TestDataGenerator:
    def test_merge_options(self):
        options_definitions = [
            {"option": "total_data_imports", "default": 16},
            {"option": "xyzzy", "default": "abcde"},
        ]
        user_options = {"total_data_imports": 4, "qwerty": "EBCDIC"}
        options, extra_options = merge_options(options_definitions, user_options)
        assert options == {"total_data_imports": 4, "xyzzy": "abcde"}
        assert extra_options == {"qwerty"}

    def test_missing_options(self):
        options_definitions = [
            {"option": "total_data_imports", "default": 16},
            {"option": "xyzzy"},
        ]
        user_options = {"total_data_imports": 4}
        with pytest.raises(DataGenNameError) as e:
            options, extra_options = merge_options(options_definitions, user_options)
        assert "xyzzy" in str(e.value)

    def test_extra_options_warning(self):
        yaml = """
        - option: total_data_imports
          default: 16
        """
        with pytest.warns(UserWarning, match="qwerty"):
            generate(StringIO(yaml), {"qwerty": "EBCDIC"})

    def test_missing_options_from_yaml(self):
        yaml = """
        - option: total_data_imports
          default: 16
        - option: xyzzy
        """
        with pytest.raises(DataGenNameError) as e:
            generate(StringIO(yaml), {"qwerty": "EBCDIC"})
        assert "xyzzy" in str(e.value)

    def test_stopping_criteria_with_startids(self, generated_rows):
        yaml = """
            - object: foo
              just_once: True
            - object: bar
            """

        continuation_yaml = """
id_manager:
  last_used_ids:
    foo: 41
    bar: 1000
nicknames_and_tables: {}
today: 2022-11-03
persistent_nicknames: {}
                """
        generate(
            StringIO(yaml),
            continuation_file=StringIO(continuation_yaml),
            stopping_criteria=StoppingCriteria("bar", 3),
        )
        assert generated_rows.mock_calls == [
            mock.call("bar", {"id": 1001}),
            mock.call("bar", {"id": 1002}),
            mock.call("bar", {"id": 1003}),
        ]

    def test_stopping_criteria_and_just_once(self, generated_rows):
        yaml = """
        - object: foo
          just_once: True
        - object: bar
        """
        generate(StringIO(yaml), stopping_criteria=StoppingCriteria("bar", 3))
        assert generated_rows.mock_calls == [
            mock.call("foo", {"id": 1}),
            mock.call("bar", {"id": 1}),
            mock.call("bar", {"id": 2}),
            mock.call("bar", {"id": 3}),
        ]

    def test_stops_on_no_progress(self, generated_rows):
        yaml = """
        - object: foo
          just_once: True
        - object: bar
        """
        with pytest.raises(RuntimeError):
            generate(StringIO(yaml), stopping_criteria=StoppingCriteria("foo", 3))

    def test_stops_if_criteria_misspelled(self, generated_rows):
        yaml = """
        - object: foo
          just_once: True
        - object: bar
        """
        with pytest.raises(DataGenError):
            generate(StringIO(yaml), stopping_criteria=StoppingCriteria("baz", 3))

    def test_nested_just_once_fails__friends(self):
        yaml = """
            - object: X
              friends:
              - object: foo
                nickname: Foo
                just_once: True
                fields:
                    A: 25
            - object: bar
              fields:
                foo_reference:
                    reference: Foo
                A: ${{Foo.A}}
            - object: baz
              fields:
                bar_reference:
                    reference: bar
            """
        continuation_file = StringIO()
        with pytest.raises(exc.DataGenSyntaxError):
            generate(StringIO(yaml), generate_continuation_file=continuation_file)

    def test_nested_just_once_fails__fields(self):
        yaml = """
            - object: X
              fields:
                xyzzy:
                    - object: foo
                        nickname: Foo
                        just_once: True
                        fields:
                            A: 25
            """
        with pytest.raises(exc.DataGenSyntaxError):
            generate(StringIO(yaml))

    def test_duplicate_names_fail(self):
        yaml = """
            - object: obj
            - object: obj2
              nickname: obj
            """
        # with pytest.raises(exc.DataGenSyntaxError):
        with pytest.warns(
            UserWarning,
            match="Should not reuse names as both nickname and table name:",
        ):
            generate(StringIO(yaml))


class TestValidationIntegration:
    """Test validation integration in data_generator"""

    def test_strict_mode_catches_validation_errors(self):
        """Test that strict_mode catches validation errors and raises exception"""
        yaml = """
        - snowfakery_version: 3
        - object: Account
          fields:
            Score:
              random_number:
                min: 100
                max: 50
        """
        from snowfakery.data_gen_exceptions import DataGenValidationError

        with pytest.raises(DataGenValidationError) as exc_info:
            generate(StringIO(yaml), strict_mode=True)

        # Should mention the validation error
        assert (
            "min" in str(exc_info.value).lower() or "max" in str(exc_info.value).lower()
        )

    def test_strict_mode_allows_valid_recipe(self):
        """Test that strict_mode allows valid recipes to execute"""
        yaml = """
        - snowfakery_version: 3
        - object: Account
          count: 2
          fields:
            Name: Test Account
            Score:
              random_number:
                min: 1
                max: 10
        """
        # Should execute without errors
        result = generate(StringIO(yaml), strict_mode=True)
        assert result is not None

    def test_validate_only_mode(self):
        """Test that validate_only performs validation and returns ValidationResult"""
        yaml = """
        - snowfakery_version: 3
        - object: Account
          fields:
            Name: Test
        """
        result = generate(StringIO(yaml), validate_only=True)

        # Should return ValidationResult, not ExecutionSummary
        assert hasattr(result, "has_errors")
        assert hasattr(result, "has_warnings")
        assert not result.has_errors()

    def test_validate_only_with_errors(self):
        """Test that validate_only detects errors without execution"""
        yaml = """
        - snowfakery_version: 3
        - object: Account
          fields:
            Score:
              random_number:
                min: 100
                max: 50
        """
        from snowfakery.data_gen_exceptions import DataGenValidationError

        with pytest.raises(DataGenValidationError):
            generate(StringIO(yaml), validate_only=True)

    def test_default_mode_no_validation(self):
        """Test that default mode (no strict_mode) doesn't perform upfront validation"""
        yaml = """
        - snowfakery_version: 3
        - object: Account
          count: 1
          fields:
            Name: Test
        """
        # Should execute normally without validation phase
        result = generate(StringIO(yaml), strict_mode=False)
        assert result is not None

    def test_validation_with_unknown_function(self):
        """Test validation catches unknown function names"""
        yaml = """
        - snowfakery_version: 3
        - object: Account
          fields:
            Value:
              unknown_function_xyz:
                param: value
        """
        from snowfakery.data_gen_exceptions import DataGenValidationError

        with pytest.raises(DataGenValidationError) as exc_info:
            generate(StringIO(yaml), strict_mode=True)

        assert "unknown" in str(exc_info.value).lower()

    def test_validation_with_reference_forward_ref(self):
        """Test validation allows forward references for reference function"""
        yaml = """
        - snowfakery_version: 3
        - object: Account
          fields:
            ContactRef:
              reference: Contact
        - object: Contact
          fields:
            Name: Test
        """
        # Should validate successfully (forward reference is allowed)
        result = generate(StringIO(yaml), strict_mode=True)
        assert result is not None

    def test_validation_with_warnings_only(self):
        """Test validation success message with warnings"""
        yaml = """
        - snowfakery_version: 3
        - object: Account
          fields:
            Value:
              random_choice:
                option1: 30%
                option2: 40%
        """
        # Should pass with warnings (probabilities don't add to 100%)
        result = generate(StringIO(yaml), strict_mode=True)
        assert result is not None
