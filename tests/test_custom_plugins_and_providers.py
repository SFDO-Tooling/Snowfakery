from io import StringIO
import math

from snowfakery.data_generator import generate
from snowfakery import SnowfakeryPlugin, lazy

from unittest import mock
import pytest

write_row_path = "snowfakery.output_streams.DebugOutputStream.write_row"


def row_values(write_row_mock, index, value):
    return write_row_mock.mock_calls[index][1][1][value]


class SimpleTestPlugin(SnowfakeryPlugin):
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
        generate(StringIO(yaml), {})
        assert row_values(write_row_mock, 0, "service_name")


class TestCustomPlugin:
    def test_bogus_plugin(self):
        yaml = """
        - plugin: tests.test_custom_plugins_and_providers.TestCustomPlugin
        - object: OBJ
          fields:
            service_name: saascrmlightning
        """
        with pytest.raises(TypeError) as e:
            generate(StringIO(yaml), {})
        assert "TestCustomPlugin" in str(e.value)

    def test_missing_plugin(self):
        yaml = """
        - plugin: xyzzy.test_custom_plugins_and_providers.TestCustomPlugin
        - object: OBJ
          fields:
            service_name: saascrmlightning
        """
        with pytest.raises(ImportError) as e:
            generate(StringIO(yaml), {})
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
        generate(StringIO(yaml), {})
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
        generate(StringIO(yaml), {})
        assert row_values(write_row_mock, 0, "pi") == math.pi

    @mock.patch(write_row_path)
    def test_math(self, write_row_mock):
        yaml = """
        - plugin: snowfakery.standard_plugins.Math
        - object: OBJ
          fields:
            twelve: ${{Math.sqrt(144)}}
        """
        generate(StringIO(yaml), {})
        assert row_values(write_row_mock, 0, "twelve") == 12

    @mock.patch(write_row_path)
    def test_math_deconstructed(self, write_row_mock):
        yaml = """
        - plugin: snowfakery.standard_plugins.Math
        - object: OBJ
          fields:
            twelve:
                Math.sqrt: 144
        """
        generate(StringIO(yaml), {})
        assert row_values(write_row_mock, 0, "twelve") == 12


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
    def test_context_vars(self, write_row):
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
        generate(StringIO(yaml), {})

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
        generate(StringIO(yaml), {})

        assert row_values(write_row, 0, "some_value") == "abc : abc"
        assert row_values(write_row, 0, "some_value_2") == "1 : 2"
