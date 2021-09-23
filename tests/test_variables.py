from unittest import mock
from io import StringIO

import pytest

from snowfakery.data_generator import generate
from snowfakery import data_gen_exceptions as exc


class TestVariables:
    def test_override_later(self, generated_rows):
        yaml = """
        - var: foo
          value: FOO
        - object: first
          fields:
            foo: ${{foo}}
        - var: foo
          value: BAR
        - object: second
          fields:
            foo: ${{foo}}
        """
        generate(StringIO(yaml))
        assert generated_rows.mock_calls == [
            mock.call("first", {"id": 1, "foo": "FOO"}),
            mock.call("second", {"id": 1, "foo": "BAR"}),
        ]

    def test_nesting_and_reset(self, generated_rows):
        yaml = """
        - var: foo
          value: FOO
        - object: first
          fields:
            foo: ${{foo}}
          friends:
          - var: foo
            value: BAR
          - object: second
            fields:
              foo: ${{foo}}
        - object: third
          fields:
            foo: ${{foo}}
        """
        generate(StringIO(yaml))
        assert generated_rows.mock_calls == [
            mock.call("first", {"id": 1, "foo": "FOO"}),
            mock.call("second", {"id": 1, "foo": "BAR"}),
            mock.call("third", {"id": 1, "foo": "FOO"}),
        ]

    def test_objects_in_vars(self, generated_rows):
        yaml = """
        - var: foo
          value:
            - object: __Foo
              fields:
                bar: BAR
        - object: first
          fields:
            foo: ${{__Foo.bar}}
        """
        generate(StringIO(yaml))
        assert generated_rows.mock_calls == [
            mock.call("first", {"id": 1, "foo": "BAR"}),
        ]

    def test_vars_depend_on_vars(self, generated_rows):
        yaml = """
        - var: foo
          value: FOO
        - var: bar
          value: ${{foo}}${{foo}}
        - object: first
          fields:
            foo: ${{foo}}
            foo2: ${{bar}}
        """
        generate(StringIO(yaml))
        assert generated_rows.mock_calls == [
            mock.call("first", {"id": 1, "foo": "FOO", "foo2": "FOOFOO"}),
        ]

    def test_just_one_misuse(self, generated_rows):
        yaml = """
        - object: first
          fields:
            foo: ${{foo}}
          friends:
            - var: foo
              just_once: True
              value: BAR
        """
        with pytest.raises(exc.DataGenError, match="just_once"):
            generate(StringIO(yaml))
