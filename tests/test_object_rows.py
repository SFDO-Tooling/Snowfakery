from unittest.mock import Mock

from snowfakery.object_rows import NicknameSlot


class TestNicknameSlot:
    def test_repr(self):
        nns = NicknameSlot("Account", Mock())
        assert "Account" in repr(nns)
