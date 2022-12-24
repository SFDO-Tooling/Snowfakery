from io import StringIO

from snowfakery.data_generator import generate


def row_values(generated_rows, index, value):
    return generated_rows.mock_calls[index][1][1][value]


class Testi18n:
    def test_i18n(self, generated_rows):
        yaml = """
        - object: foo
          fields:
            japanese_name:
                i18n_fake:
                    locale: ja_JP
                    fake: name"""
        generate(StringIO(yaml), {})
        assert isinstance(row_values(generated_rows, 0, "japanese_name"), str)
