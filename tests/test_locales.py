from unittest import mock
from io import StringIO
from faker import Faker

from snowfakery.data_generator import generate


class TestLocales:
    def test_locales(self, generated_rows):
        yaml = """
        - var: snowfakery_locale
          value: no_NO
        - object: first
          fields:
            name:
              fake: name
        - var: snowfakery_locale
          value: fr_FR
        - object: second
          fields:
            name:
              fake: name
        """
        with mock.patch("snowfakery.fakedata.fake_data_generator.Faker") as f:

            class FakeFaker(Faker):
                def name(self):
                    return "xyzzy"

            f.return_value = FakeFaker()
            generate(StringIO(yaml))
            locale_changes = [c[1][0] for c in f.mock_calls if not c[0]]

            assert locale_changes == [None, "no_NO", "fr_FR"]
