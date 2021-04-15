import unittest
from unittest import mock
from io import StringIO

import pytest

from snowfakery.data_generator import merge_options, generate
from snowfakery.data_gen_exceptions import DataGenNameError, DataGenError
from snowfakery.data_generator_runtime import StoppingCriteria
from snowfakery import data_gen_exceptions as exc


class TestDataGenerator(unittest.TestCase):
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
        with self.assertRaises(DataGenNameError) as e:
            options, extra_options = merge_options(options_definitions, user_options)
        assert "xyzzy" in str(e.exception)

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
        with self.assertRaises(DataGenNameError) as e:
            generate(StringIO(yaml), {"qwerty": "EBCDIC"})
        assert "xyzzy" in str(e.exception)

    @mock.patch("snowfakery.output_streams.DebugOutputStream.write_row")
    def test_stopping_criteria_with_startids(self, write_row):
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
        assert write_row.mock_calls == [
            mock.call("bar", {"id": 1001}),
            mock.call("bar", {"id": 1002}),
            mock.call("bar", {"id": 1003}),
        ]

    @mock.patch("snowfakery.output_streams.DebugOutputStream.write_row")
    def test_stopping_criteria_and_just_once(self, write_row):
        yaml = """
        - object: foo
          just_once: True
        - object: bar
        """
        generate(StringIO(yaml), stopping_criteria=StoppingCriteria("bar", 3))
        assert write_row.mock_calls == [
            mock.call("foo", {"id": 1}),
            mock.call("bar", {"id": 1}),
            mock.call("bar", {"id": 2}),
            mock.call("bar", {"id": 3}),
        ]

    @mock.patch("snowfakery.output_streams.DebugOutputStream.write_row")
    def test_stops_on_no_progress(self, write_row):
        yaml = """
        - object: foo
          just_once: True
        - object: bar
        """
        with self.assertRaises(RuntimeError):
            generate(StringIO(yaml), stopping_criteria=StoppingCriteria("foo", 3))

    @mock.patch("snowfakery.output_streams.DebugOutputStream.write_row")
    def test_stops_if_criteria_misspelled(self, write_row):
        yaml = """
        - object: foo
          just_once: True
        - object: bar
        """
        with self.assertRaises(DataGenError):
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
        with self.assertRaises(exc.DataGenSyntaxError):
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
        with self.assertRaises(exc.DataGenSyntaxError):
            generate(StringIO(yaml))
