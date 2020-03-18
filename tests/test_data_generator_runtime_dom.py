import unittest
from snowfakery.data_generator_runtime_dom import (
    FieldFactory,
    SimpleValue,
    StructuredValue,
    ObjectTemplate,
    DataGenError,
)

from snowfakery.data_generator_runtime import RuntimeContext, Globals

from snowfakery.output_streams import DebugOutputStream

from snowfakery.utils.template_utils import FakerTemplateLibrary

ftl = FakerTemplateLibrary([])

x = RuntimeContext(Globals(), "Foo", ftl)
line = {"filename": "abc.yml", "line_num": 42}


class TestDataGeneratorRuntimeDom(unittest.TestCase):
    def test_field_factory_string(self):
        definition = SimpleValue("abc", "abc.yml", 10)
        repr(definition)
        f = FieldFactory("field", definition, "abc.yml", 10)
        repr(f)
        x = f.generate_value(RuntimeContext(Globals(), "Foo", ftl))
        assert x == "abc"

    def test_field_factory_int(self):
        definition = SimpleValue(5, "abc.yml", 10)
        repr(definition)
        f = FieldFactory("field", definition, "abc.yml", 10)
        repr(f)
        x = f.generate_value(RuntimeContext(Globals(), "Foo", ftl))
        assert x == 5

    def test_field_factory_calculation(self):
        definition = SimpleValue("<<5*3>>", "abc.yml", 10)
        repr(definition)
        f = FieldFactory("field", definition, "abc.yml", 10)
        repr(f)
        x = f.generate_value(RuntimeContext(Globals(), "foo", ftl))
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
        x = f.generate_value(RuntimeContext(Globals(), "Foo", ftl))
        assert x in ["abc", "def"]

    def test_render_empty_object_template(self):
        o = ObjectTemplate("abcd", filename="abc.yml", line_num=10)
        o.generate_rows(DebugOutputStream(), RuntimeContext(Globals(), "Foo", ftl))

    def test_fail_render_object_template(self):
        o = ObjectTemplate("abcd", filename="abc.yml", line_num=10)
        with self.assertRaises(DataGenError):
            o.generate_rows(None, RuntimeContext(Globals(), "Foo", ftl))

    def test_fail_render_weird_type(self):
        with self.assertRaises((DataGenError, TypeError)):
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
            o.generate_rows(DebugOutputStream(), RuntimeContext(None, "Foo"))

    def test_fail_render_weird_template(self):
        with self.assertRaises(DataGenError):
            o = ObjectTemplate(
                "abcd",
                filename="abc.yml",
                line_num=10,
                fields=[
                    FieldFactory(
                        "x",
                        SimpleValue("<<5()>>", filename="abc.yml", line_num=42),
                        **line
                    )
                ],
            )
            o.generate_rows(DebugOutputStream(), RuntimeContext(Globals(), "Foo", ftl))

    def test_structured_value_errors(self):
        with self.assertRaises(DataGenError) as e:
            StructuredValue("this.that.foo", [], **line).render(
                RuntimeContext(Globals(), "Foo", ftl)
            )
        assert "only one" in str(e.exception)

        with self.assertRaises(DataGenError) as e:
            StructuredValue("bar", [], **line).render(
                RuntimeContext(Globals(), "Foo", ftl)
            )
        assert "Cannot find func" in str(e.exception)
        assert "bar" in str(e.exception)

        with self.assertRaises(DataGenError) as e:
            StructuredValue("xyzzy.abc", [], **line).render(
                RuntimeContext(Globals(), "Foo", ftl)
            )
        assert "Cannot find defini" in str(e.exception)
        assert "xyzzy" in str(e.exception)

        with self.assertRaises(DataGenError) as e:
            StructuredValue("this.abc", [], **line).render(
                RuntimeContext(Globals(), "Foo", ftl)
            )
        assert "Cannot find defini" in str(e.exception)
        assert "abc" in str(e.exception)
