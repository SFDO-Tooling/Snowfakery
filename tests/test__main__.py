import pytest


class TestMainModule:
    def test_main_module(self, capsys):
        with pytest.raises(SystemExit):
            from snowfakery import __main__ as _unused

            _unused = _unused  # flake8

        assert "Usage:" in capsys.readouterr().err
