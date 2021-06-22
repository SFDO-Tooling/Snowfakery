from snowfakery.data_gen_exceptions import DataGenError


class TestExceptions:
    def test_stringify_DataGenError(self):
        val = str(DataGenError("Blah", "foo.yml", 25))
        assert "Blah" in val
        assert "foo.yml" in val
        assert "25" in val

        val = str(DataGenError("Blah", "foo.yml"))
        assert "Blah" in val
        assert "foo.yml" in val
