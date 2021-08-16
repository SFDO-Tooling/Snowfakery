from io import StringIO
import math
import operator
from base64 import b64decode

from snowfakery import SnowfakeryPlugin, lazy
from snowfakery.plugins import PluginResult, PluginOption
from snowfakery.data_gen_exceptions import (
    DataGenError,
    DataGenTypeError,
    DataGenImportError,
)
from snowfakery import generate_data

generate = generate_data

from unittest import mock
import pytest

write_row_path = "snowfakery.output_streams.DebugOutputStream.write_row"


def row_values(write_row_mock, index, value):
    return write_row_mock.mock_calls[index][1][1][value]


class SimpleTestPlugin(SnowfakeryPlugin):
    allowed_options = [
        PluginOption(
            "tests.test_custom_plugins_and_providers.SimpleTestPlugin.option_str", str
        ),
        PluginOption(
            "tests.test_custom_plugins_and_providers.SimpleTestPlugin.option_int", int
        ),
    ]

    class Functions:
        def double(self, value):
            return value * 2


class DoubleVisionPlugin(SnowfakeryPlugin):
    class Functions:
        @lazy
        def do_it_twice(self, value):
            "Evaluates its argument twice into a string"
            rc = f"{self.context.evaluate(value)} : {self.context.evaluate(value)}"

            return rc


class WrongTypePlugin(SnowfakeryPlugin):
    class Functions:
        def return_bad_type(self, value):
            "Evaluates its argument twice into a string"
            return int  # function

        junk = None


class MyEvaluator(PluginResult):
    def __init__(self, operator, *operands):
        super().__init__({"operator": operator, "operands": operands})

    def _eval(self):
        op = getattr(operator, self.result["operator"])
        vals = self.result["operands"]
        rc = op(*vals)
        return self.result.setdefault("value", str(rc))

    def __str__(self):
        return str(self._eval())

    def simplify(self):
        return int(self._eval())


class EvalPlugin(SnowfakeryPlugin):
    class Functions:
        @lazy
        def add(self, val1, val2):
            return MyEvaluator(
                "add", self.context.evaluate(val1), self.context.evaluate(val2)
            )

        @lazy
        def sub(self, val1, val2):
            return MyEvaluator(
                "sub", self.context.evaluate(val1), self.context.evaluate(val2)
            )


class TestCustomFakerProvider:
    @mock.patch(write_row_path)
    def test_custom_faker_provider(self, write_row_mock):
        yaml = """
        - plugin: faker_microservice.Provider
        - object: OBJ
          fields:
            service_name:
                fake:
                    microservice
        """
        generate_data(StringIO(yaml))
        assert row_values(write_row_mock, 0, "service_name")


class TestCustomPlugin:
    def test_bogus_plugin(self):
        yaml = """
        - plugin: tests.test_custom_plugins_and_providers.TestCustomPlugin
        - object: OBJ
          fields:
            service_name: saascrmlightning
        """
        with pytest.raises(DataGenTypeError) as e:
            generate_data(StringIO(yaml))
        assert "TestCustomPlugin" in str(e.value)
        assert ":2" in str(e.value)

    def test_missing_plugin(self):
        yaml = """
        - plugin: xyzzy.test_custom_plugins_and_providers.TestCustomPlugin
        - object: OBJ
          fields:
            service_name: saascrmlightning
        """
        with pytest.raises(DataGenImportError) as e:
            generate_data(StringIO(yaml))
        assert "xyzzy" in str(e.value)

    @mock.patch(write_row_path)
    def test_simple_plugin(self, write_row_mock):
        yaml = """
        - plugin: tests.test_custom_plugins_and_providers.SimpleTestPlugin
        - object: OBJ
          fields:
            four:
                SimpleTestPlugin.double: 2
            six: ${{SimpleTestPlugin.double(3)}}
        """
        generate_data(StringIO(yaml))
        assert row_values(write_row_mock, 0, "four") == 4
        assert row_values(write_row_mock, 0, "six") == 6

    @mock.patch(write_row_path)
    def test_constants(self, write_row_mock):
        yaml = """
        - plugin: snowfakery.standard_plugins.Math
        - object: OBJ
          fields:
            pi: ${{Math.pi}}
        """
        generate_data(StringIO(yaml))
        assert row_values(write_row_mock, 0, "pi") == math.pi

    @mock.patch(write_row_path)
    def test_math(self, write_row_mock):
        yaml = """
        - plugin: snowfakery.standard_plugins.Math
        - object: OBJ
          fields:
            sqrt: ${{Math.sqrt(144)}}
            max: ${{Math.max(144, 200, 100)}}
            eleven: ${{Math.round(10.7)}}
            min: ${{Math.min(144, 200, 100)}}
        """
        generate_data(StringIO(yaml))
        assert row_values(write_row_mock, 0, "sqrt") == 12
        assert row_values(write_row_mock, 0, "max") == 200
        assert row_values(write_row_mock, 0, "eleven") == 11
        assert row_values(write_row_mock, 0, "min") == 100

    @mock.patch(write_row_path)
    def test_math_deconstructed(self, write_row_mock):
        yaml = """
        - plugin: snowfakery.standard_plugins.Math
        - object: OBJ
          fields:
            twelve:
                Math.sqrt: ${{Math.min(144, 169)}}
        """
        generate_data(StringIO(yaml))
        assert row_values(write_row_mock, 0, "twelve") == 12

    @mock.patch(write_row_path)
    def test_stringification(self, write_row):
        yaml = """
        - plugin: tests.test_custom_plugins_and_providers.EvalPlugin
        - object: OBJ
          fields:
            some_value:
                - EvalPlugin.add:
                    - 1
                    - EvalPlugin.sub:
                        - 5
                        - 3
        """
        with StringIO() as s:
            generate_data(StringIO(yaml), output_file=s, output_format="json")
            assert eval(s.getvalue())[0]["some_value"] == 3

    def test_binary(self, generated_rows):
        sample = "examples/binary.recipe.yml"
        with open(sample) as f:
            generate(f)
        b64data = generated_rows.table_values("BinaryData", 0)["encoded_data"]
        rawdata = b64decode(b64data)
        assert rawdata.startswith(b"%PDF-1.3")
        assert b"Helvetica" in rawdata

    def test_option__simple(self, generated_rows):
        yaml = """-  plugin: tests.test_custom_plugins_and_providers.SimpleTestPlugin"""

        generate_data(StringIO(yaml), plugin_options={"option_str": "AAA"})

    def test_option__unknown(self, generated_rows):
        yaml = """-  plugin: tests.test_custom_plugins_and_providers.SimpleTestPlugin"""

        generate_data(StringIO(yaml), plugin_options={"option_str": "zzz"})

    def test_option__bad_type(self, generated_rows):
        yaml = """-  plugin: tests.test_custom_plugins_and_providers.SimpleTestPlugin"""
        with pytest.raises(DataGenTypeError):
            generate_data(StringIO(yaml), plugin_options={"option_int": "abcd"})

    def test_option_type_coercion_needed(self, generated_rows):
        yaml = """-  plugin: tests.test_custom_plugins_and_providers.SimpleTestPlugin"""

        generate_data(StringIO(yaml), plugin_options={"option_int": "5"})


class PluginThatNeedsState(SnowfakeryPlugin):
    class Functions:
        def object_path(self):
            context = self.context
            context_vars = context.context_vars()
            current_value = context_vars.setdefault("object_path", "ROOT")
            field_vars = context.field_vars()
            new_value = current_value + "." + field_vars["this"].name
            context_vars["object_path"] = new_value
            return new_value

        def count(self):
            context_vars = self.context.context_vars()
            context_vars.setdefault("count", 0)
            context_vars["count"] += 1
            return context_vars["count"]


class TestContextVars:
    @mock.patch(write_row_path)
    def test_plugin_context_vars(self, write_row):
        yaml = """
        - plugin: tests.test_custom_plugins_and_providers.PluginThatNeedsState
        - object: OBJ
          fields:
            name: OBJ1
            path: ${{PluginThatNeedsState.object_path()}}
            child:
                - object: OBJ
                  fields:
                    name: OBJ2
                    path: ${{PluginThatNeedsState.object_path()}}
        - object: OBJ
          fields:
            name: OBJ3
            path: ${{PluginThatNeedsState.object_path()}}
            child:
                - object: OBJ
                  fields:
                    name: OBJ4
                    path: ${{PluginThatNeedsState.object_path()}}
        """
        generate_data(StringIO(yaml))

        assert row_values(write_row, 0, "path") == "ROOT.OBJ1.OBJ2"
        assert row_values(write_row, 1, "path") == "ROOT.OBJ1"
        assert row_values(write_row, 2, "path") == "ROOT.OBJ3.OBJ4"
        assert row_values(write_row, 3, "path") == "ROOT.OBJ3"

    @mock.patch(write_row_path)
    def test_lazy_with_context(self, write_row):
        yaml = """
        - plugin: tests.test_custom_plugins_and_providers.DoubleVisionPlugin
        - plugin: tests.test_custom_plugins_and_providers.PluginThatNeedsState
        - object: OBJ
          fields:
            some_value:
                - DoubleVisionPlugin.do_it_twice:
                    - abc
            some_value_2:
                - DoubleVisionPlugin.do_it_twice:
                    - ${{PluginThatNeedsState.count()}}
        """
        generate_data(StringIO(yaml))

        assert row_values(write_row, 0, "some_value") == "abc : abc"
        assert row_values(write_row, 0, "some_value_2") == "1 : 2"

    def test_weird_types(self):
        yaml = """
        - plugin: tests.test_custom_plugins_and_providers.WrongTypePlugin  # 2
        - object: B                             #3
          fields:                               #4
            foo:                                #5
                WrongTypePlugin.return_bad_type: 5  #6
        """
        with pytest.raises(DataGenError) as e:
            generate_data(StringIO(yaml))
        assert 6 > e.value.line_num >= 3

    def test_plugin_paths(self, generated_rows):
        generate_data("tests/test_plugin_paths.yml")

    def test_missing_attributes(self):
        yaml = """
        - plugin: tests.test_custom_plugins_and_providers.WrongTypePlugin  # 2
        - object: B                             #3
          fields:                               #4
            foo:                                #5
                WrongTypePlugin.abcdef: 5  #6
        """
        with pytest.raises(DataGenError) as e:
            generate_data(StringIO(yaml))
        assert 6 > e.value.line_num >= 3

    def test_null_attributes(self):
        yaml = """
        - plugin: tests.test_custom_plugins_and_providers.WrongTypePlugin  # 2
        - object: B                             #3
          fields:                               #4
            foo:                                #5
                WrongTypePlugin.junk: 5  #6
        """
        with pytest.raises(DataGenError) as e:
            generate_data(StringIO(yaml))
        assert 6 > e.value.line_num >= 3
