from snowfakery.utils.template_utils import look_for_number, StringGenerator
from snowfakery.data_generator import generate
from io import StringIO


class TestParseNumbers:
    def test_parse_int(self):
        assert look_for_number("7") == 7
        assert look_for_number("7") != "7"
        assert look_for_number("09") == 9

    def test_parse_float(self):
        assert look_for_number("7.3") == 7.3
        assert look_for_number("09.9") == 9.9

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

    def test_slice(self, generated_rows):
        yaml = """
            - object: Account
              fields:
                BillingCity: ${{fake.Sentence[0:5]}}
        """

        generate(StringIO(yaml), {})
        assert len(generated_rows.table_values("Account", 0, "BillingCity")) <= 5
