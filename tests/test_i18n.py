from io import StringIO
from unittest import mock

from snowfakery.data_generator import generate

write_row_path = "snowfakery.output_streams.DebugOutputStream.write_row"


def row_values(write_row_mock, index, value):
    return write_row_mock.mock_calls[index][1][1][value]


class Testi18n:
    @mock.patch(write_row_path)
    def test_i18n(self, write_row_mock):
        yaml = """
        - object: foo
          fields:
            japanese_name:
                i18n_fake:
                    locale: ja_JP
                    fake: name"""
        generate(StringIO(yaml), {})
        assert isinstance(row_values(write_row_mock, 0, "japanese_name"), str)
