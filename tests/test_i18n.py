from io import StringIO

from snowfakery.data_generator import generate


def row_values(write_row, index, value):
    return write_row.mock_calls[index][1][1][value]


class Testi18n:
    def test_i18n(self, write_row):
        yaml = """
        - object: foo
          fields:
            japanese_name:
                i18n_fake:
                    locale: ja_JP
                    fake: name"""
        generate(StringIO(yaml), {})
        assert isinstance(row_values(write_row, 0, "japanese_name"), str)
