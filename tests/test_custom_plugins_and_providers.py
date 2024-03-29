import gc
import math
import operator
import time
from base64 import b64decode
from io import StringIO
from unittest import mock

import pytest

from snowfakery import SnowfakeryPlugin, generate_data, lazy
from snowfakery.data_gen_exceptions import (
    DataGenError,
    DataGenImportError,
    DataGenTypeError,
)
from snowfakery.plugins import (
    PluginOption,
    PluginResult,
    PluginResultIterator,
    memorable,
)

generate = generate_data


def row_values(generated_rows, index, value):
    return generated_rows.mock_calls[index][1][1][value]


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

        @memorable
        def fib(self, value):
            return FibIterator()


class FibIterator(PluginResultIterator):
    def __init__(self):
        self.a = 1
        self.b = 1

    def close(self):
        self.a = None
        self.b = None

    def next(self):
        self.a, self.b = self.b, self.a + self.b
        return self.b


class DoubleVisionPlugin(SnowfakeryPlugin):
    class Functions:
        @lazy
        def do_it_twice(self, value):
            "Evaluates its argument twice into a string"
            rc = f"{self.context.evaluate(value)} : {self.context.evaluate(value)}"

            return rc


class WrongTypePlugin(SnowfakeryPlugin):
    class Functions:
        foo = 5

        def return_bad_type(self, value):
            "Evaluates its argument twice into a string"
            return int  # function


class TimeStampPlugin(SnowfakeryPlugin):
    class Functions:
        @memorable
        def constant_time(self, value=None, name=None):
            "Return the current time and then remember it."
            time.sleep(0.01)
            return time.time()


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


class DoesNotClosePlugin(SnowfakeryPlugin):
    close = NotImplemented

    class Functions:
        def foo(self, a=None):
            return None


class TestCustomFakerProvider:
    def test_custom_faker_provider(self, generated_rows):
        yaml = """
        - plugin: faker_microservice.Provider
        - object: OBJ
          fields:
            service_name:
                fake:
                    microservice
        """
        generate_data(StringIO(yaml))
        assert row_values(generated_rows, 0, "service_name")


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

    def test_simple_plugin(self, generated_rows):
        yaml = """
        - plugin: tests.test_custom_plugins_and_providers.SimpleTestPlugin
        - object: OBJ
          fields:
            four:
                SimpleTestPlugin.double: 2
            six: ${{SimpleTestPlugin.double(3)}}
        """
        generate_data(StringIO(yaml))
        assert row_values(generated_rows, 0, "four") == 4
        assert row_values(generated_rows, 0, "six") == 6

    def test_constants(self, generated_rows):
        yaml = """
        - plugin: snowfakery.standard_plugins.Math
        - object: OBJ
          fields:
            pi: ${{Math.pi}}
        """
        generate_data(StringIO(yaml))
        assert row_values(generated_rows, 0, "pi") == math.pi

    def test_math(self, generated_rows):
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
        assert row_values(generated_rows, 0, "sqrt") == 12
        assert row_values(generated_rows, 0, "max") == 200
        assert row_values(generated_rows, 0, "eleven") == 11
        assert row_values(generated_rows, 0, "min") == 100

    def test_math_deconstructed(self, generated_rows):
        yaml = """
        - plugin: snowfakery.standard_plugins.Math
        - object: OBJ
          fields:
            twelve:
                Math.sqrt: ${{Math.min(144, 169)}}
        """
        generate_data(StringIO(yaml))
        assert row_values(generated_rows, 0, "twelve") == 12

    def test_stringification(self, generated_rows):
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
    def test_plugin_context_vars(self, generated_rows):
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

        assert row_values(generated_rows, 0, "path") == "ROOT.OBJ1.OBJ2"
        assert row_values(generated_rows, 1, "path") == "ROOT.OBJ1"
        assert row_values(generated_rows, 2, "path") == "ROOT.OBJ3.OBJ4"
        assert row_values(generated_rows, 3, "path") == "ROOT.OBJ3"

    def test_lazy_with_context(self, generated_rows):
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

        assert row_values(generated_rows, 0, "some_value") == "abc : abc"
        assert row_values(generated_rows, 0, "some_value_2") == "1 : 2"

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
        assert e.value.line_num
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
        assert e.value.line_num
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
        assert e.value.line_num
        assert 6 > e.value.line_num >= 3

    def test_not_callable_attributes(self):
        yaml = """
        - plugin: tests.test_custom_plugins_and_providers.WrongTypePlugin  # 2
        - object: B                             #3
          fields:                               #4
            foo:                                #5
                WrongTypePlugin.foo: 5  #6
        """
        with pytest.raises(DataGenError, match="Cannot call") as e:
            generate_data(StringIO(yaml))
        assert e.value.line_num
        assert 6 > e.value.line_num >= 3

    def test_memorable_plugin(self, generated_rows):
        yaml = """
        - plugin: tests.test_custom_plugins_and_providers.TimeStampPlugin
        - object: B
          count: 5
          fields:
            foo:
                TimeStampPlugin.constant_time:
        """
        generate_data(StringIO(yaml))
        assert generated_rows.table_values(
            "B", 1, "foo"
        ) == generated_rows.table_values("B", 5, "foo")

    def test_memorable_plugin__scopes(self, generated_rows):
        yaml = """
        - plugin: tests.test_custom_plugins_and_providers.TimeStampPlugin
        - object: A
          fields:
            foo:
                TimeStampPlugin.constant_time:
                    value: BLAH
                    name: A
        - object: B
          fields:
            foo:
                TimeStampPlugin.constant_time:
        - object: C
          fields:
            foo:
                TimeStampPlugin.constant_time:
        - object: D
          count: 3
          fields:
            foo:
                TimeStampPlugin.constant_time:
                    name: A

        """
        generate_data(StringIO(yaml))
        assert generated_rows.table_values(
            "A", 1, "foo"
        ) == generated_rows.table_values("D", 3, "foo")
        assert generated_rows.table_values(
            "A", 1, "foo"
        ) != generated_rows.table_values("B", 1, "foo")
        assert generated_rows.table_values(
            "B", 1, "foo"
        ) != generated_rows.table_values("C", 1, "foo")

    def test_plugin_does_not_close(self):
        yaml = """
        - plugin: tests.test_custom_plugins_and_providers.DoesNotClosePlugin
        - object: B
          fields:
            foo:
                DoesNotClosePlugin.foo:
        """
        with pytest.warns(UserWarning, match="close"):
            generate_data(StringIO(yaml))


class TestPluginResultIterator:
    @mock.patch(
        "tests.test_custom_plugins_and_providers.FibIterator.close",
    )
    def test_plugin_result_iterator__closes(self, close, generated_rows):
        yaml = """
        - plugin: tests.test_custom_plugins_and_providers.SimpleTestPlugin
        - object: OBJ
          fields:
            fibnum:
                SimpleTestPlugin.fib:
        """
        # it's better if closing of objects is triggered at a predictable
        # time by the refcounter instead of by the cyclic GC
        try:
            gc.disable()
            generate_data(StringIO(yaml), target_number=("OBJ", 3))
            assert generated_rows.table_values("OBJ", field="fibnum") == [2, 3, 5]
            assert len(close.mock_calls) == 1
        finally:
            gc.enable()
