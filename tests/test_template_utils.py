from snowfakery.utils.template_utils import look_for_number, StringGenerator


class TestParseNumbers:
    def test_parse_int(self):
        assert look_for_number("7") == 7
        assert look_for_number("7") != "7"
        assert look_for_number("09") == "09"

    def test_parse_float(self):
        assert look_for_number("7.3") == 7.3
        assert look_for_number("09.9") == "09.9"

    def test_do_not_parse_phone_number(self):
        assert look_for_number("117.344.3333") == "117.344.3333"


class TestTemplateUtils:
    def test_add(self):
        assert (
            str(StringGenerator(lambda: "a") + " " + StringGenerator(lambda: "b"))
            == "a b"
        )

    def test_self_add(self):
        assert str(StringGenerator(lambda: "a") + StringGenerator(lambda: "b")) == "ab"
