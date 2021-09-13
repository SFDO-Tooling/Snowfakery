import pytest
from unittest import mock
from snowfakery.data_generator_runtime_object_model import (
    FieldFactory,
    SimpleValue,
    StructuredValue,
    ObjectTemplate,
    DataGenError,
    DataGenValueError,
)
from snowfakery.parse_recipe_yaml import ParseResult
from snowfakery.data_generator_runtime import (
    RuntimeContext,
    Interpreter,
    Globals,
)

from snowfakery.api import SnowfakeryApplication

from snowfakery.output_streams import DebugOutputStream


line = {"filename": "abc.yml", "line_num": 42}


class FakeParseResult(ParseResult):
    def __init__(self):
        self.tables = ()
        self.templates = ()
        self.statements = ()


def standard_runtime():
    output_stream = DebugOutputStream()
    interpreter = Interpreter(
        output_stream=output_stream,
        parent_application=SnowfakeryApplication(),
        parse_result=FakeParseResult(),
        globals=Globals(),
    )
    runtime_context = RuntimeContext(interpreter=interpreter)
    interpreter.current_context = runtime_context
    return runtime_context


x = standard_runtime()


class TestDataGeneratorRuntimeDom:
    def test_field_recipe_string(self):
        definition = SimpleValue("abc", "abc.yml", 10)
        repr(definition)
        f = FieldFactory("field", definition, "abc.yml", 10)
        repr(f)
        x = f.generate_value(standard_runtime())
        assert x == "abc"

    def test_field_recipe_int(self):
        definition = SimpleValue(5, "abc.yml", 10)
        repr(definition)
        f = FieldFactory("field", definition, "abc.yml", 10)
        repr(f)
        x = f.generate_value(standard_runtime())
        assert x == 5

    def test_field_recipe_calculation(self):
        definition = SimpleValue("${{5*3}}", "abc.yml", 10)
        repr(definition)
        f = FieldFactory("field", definition, "abc.yml", 10)
        repr(f)
        x = f.generate_value(standard_runtime())
        assert x == 15

    def test_structured_value(self):
        definition = StructuredValue(
            "random_choice",
            [SimpleValue("abc", "", 1), SimpleValue("def", "", 1)],
            "abc.yml",
            10,
        )
        repr(definition)
        f = FieldFactory("field", definition, "abc.yml", 10)
        x = f.generate_value(standard_runtime())
        assert x in ["abc", "def"]

    def test_render_empty_object_template(self):
        o = ObjectTemplate("abcd", filename="abc.yml", line_num=10)
        o.generate_rows(DebugOutputStream(), standard_runtime())

    def test_fail_render_object_template(self):
        o = ObjectTemplate("abcd", filename="abc.yml", line_num=10)
        with pytest.raises(DataGenError):
            o.generate_rows(None, standard_runtime())

    def test_fail_render_weird_type(self):
        with pytest.raises((DataGenError, TypeError)):
            o = ObjectTemplate(
                "abcd",
                filename="abc.yml",
                line_num=10,
                fields=[
                    FieldFactory(
                        "x",
                        SimpleValue(b"junk", filename="abc.yml", line_num=42),
                        **line
                    )
                ],
            )
            o.generate_rows(DebugOutputStream(), standard_runtime())

    def test_fail_render_weird_template(self):
        with pytest.raises(DataGenError):
            o = ObjectTemplate(
                "abcd",
                filename="abc.yml",
                line_num=10,
                fields=[
                    FieldFactory(
                        "x",
                        SimpleValue("${{5()}}", filename="abc.yml", line_num=42),
                        **line
                    )
                ],
            )
            o.generate_rows(DebugOutputStream(), standard_runtime())

    def test_structured_value_errors(self):
        with pytest.raises(DataGenError) as e:
            StructuredValue("this.that.foo", [], **line).render(standard_runtime())
        assert "only one" in str(e.value)

        with pytest.raises(DataGenError) as e:
            StructuredValue("bar", [], **line).render(standard_runtime())
        assert "Cannot find func" in str(e.value)
        assert "bar" in str(e.value)

        with pytest.raises(DataGenError) as e:
            StructuredValue("xyzzy.abc", [], **line).render(standard_runtime())
        assert "Cannot find defini" in str(e.value)
        assert "xyzzy" in str(e.value)

        with pytest.raises(DataGenError) as e:
            StructuredValue("this.abc", [], **line).render(standard_runtime())
        assert "Cannot find defini" in str(e.value)
        assert "abc" in str(e.value)

    def test_old_jinja_syntax(self):
        definition = SimpleValue("<<5*3>>", "abc.yml", 10)
        repr(definition)
        f = FieldFactory("field", definition, "abc.yml", 10)
        repr(f)
        x = f.generate_value(standard_runtime())
        assert x == 15

    def test_mixed_jinja_syntax(self):
        definition = SimpleValue("${{2+3}} <<5*3>>", "abc.yml", 10)
        repr(definition)
        f = FieldFactory("field", definition, "abc.yml", 10)
        repr(f)
        x = f.generate_value(standard_runtime())
        assert x == "5 <<5*3>>"

    def test_check_type(self):
        o = ObjectTemplate("abcd", filename="abc.yml", line_num=10)
        field = mock.MagicMock()
        field.name = "foo"
        with pytest.raises(DataGenValueError):
            o._check_type(field, int, standard_runtime())
