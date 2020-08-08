import unittest
from unittest import mock
from os import fsencode, path

from snowfakery.parse_recipe_yaml import (
    parse_element,
    categorize_top_level_objects,
    ParseContext,
    LineTracker,
    parse_file,
)
from snowfakery.data_gen_exceptions import DataGenError
from tempfile import TemporaryDirectory

linenum = {"__line__": LineTracker("f", 5)}


class TestParseElement(unittest.TestCase):
    def test_parse_element(self):
        result = parse_element(
            {"object": "a", "b": "c", **linenum},
            "object",
            {"b": str},
            {},
            ParseContext(),
        )
        assert result.b == "c"

    def test_missing_element(self):
        # b is missing
        with self.assertRaises(DataGenError):
            parse_element(
                {"object": "a", **linenum}, "object", {"b": str}, {}, ParseContext()
            )

    def test_unknown_element(self):
        # b is missing
        with self.assertRaises(DataGenError):
            parse_element(
                {"object": "a", "q": "z", **linenum}, "object", {}, {}, ParseContext()
            )

    def test_optional_element(self):
        # b is missing
        result = parse_element(
            {"object": "a", "q": "z", **linenum},
            "object",
            {},
            {"q": str},
            ParseContext(),
        )
        assert result.q == "z"

    def test_defaulted_element(self):
        # q should be defaulted
        result = parse_element(
            {"object": "a", **linenum}, "object", {}, {"q": str}, ParseContext()
        )
        assert result.q is None


class TestCategorizeTopLevelObjects(unittest.TestCase):
    def test_categorize_top_level_objects(self):
        objects = [{"object": "a", **linenum}]
        tlos = categorize_top_level_objects(objects, ParseContext())
        assert tlos["object"][0]["object"] == "a"

    def test_unknown_top_level_objects(self):
        with self.assertRaises(DataGenError):
            objects = [{"unknown": "a", **linenum}]
            categorize_top_level_objects(objects, ParseContext())


class TestFilesystem:
    def test_funny_filenames(self):
        with TemporaryDirectory() as d:
            clownface = "🤡"
            for p, filename in [(d, clownface), (fsencode(d), fsencode(clownface))]:
                file_with_path = path.join(p, filename)
                with open(file_with_path, "w") as tempfile:

                    def mock_safe_load(stream, path):
                        assert clownface in path
                        return [], {}

                    with mock.patch(
                        "snowfakery.parse_recipe_yaml.yaml_safe_load_with_line_numbers",
                        mock_safe_load,
                    ):
                        parse_file(tempfile, ParseContext())
