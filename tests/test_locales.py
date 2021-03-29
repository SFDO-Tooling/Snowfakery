from unittest import mock
from io import StringIO

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
        with mock.patch("snowfakery.utils.template_utils.make_faker") as f:
            generate(StringIO(yaml))
            locale_changes = [c[1][0] for c in f.mock_calls if not c[0]]

            assert locale_changes == [None, "no_NO", "fr_FR"]
