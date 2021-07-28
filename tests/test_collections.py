from snowfakery.utils.collections import CaseInsensitiveDict
import pytest


# From: https://github.com/psf/requests/blob/05a1a21593c9c8e79393d35fae12c9c27a6f7605/tests/test_requests.py
class TestCaseInsensitiveDict:
    @pytest.mark.parametrize(
        "cid",
        (
            CaseInsensitiveDict({"Foo": "foo", "BAr": "bar"}),
            CaseInsensitiveDict([("Foo", "foo"), ("BAr", "bar")]),
            CaseInsensitiveDict(FOO="foo", BAr="bar"),
        ),
    )
    def test_init(self, cid):
        assert len(cid) == 2
        assert "foo" in cid
        assert "bar" in cid

    def test_docstring_example(self):
        cid = CaseInsensitiveDict()
        cid["Accept"] = "application/json"
        assert cid["aCCEPT"] == "application/json"
        assert list(cid) == ["Accept"]

    def test_len(self):
        cid = CaseInsensitiveDict({"a": "a", "b": "b"})
        cid["A"] = "a"
        assert len(cid) == 2

    def test_getitem(self):
        cid = CaseInsensitiveDict({"Spam": "blueval"})
        assert cid["spam"] == "blueval"
        assert cid["SPAM"] == "blueval"

    def test_fixes_649(self):
        """__setitem__ should behave case-insensitively."""
        cid = CaseInsensitiveDict()
        cid["spam"] = "oneval"
        cid["Spam"] = "twoval"
        cid["sPAM"] = "redval"
        cid["SPAM"] = "blueval"
        assert cid["spam"] == "blueval"
        assert cid["SPAM"] == "blueval"
        assert list(cid.keys()) == ["SPAM"]

    def test_delitem(self):
        cid = CaseInsensitiveDict()
        cid["Spam"] = "someval"
        del cid["sPam"]
        assert "spam" not in cid
        assert len(cid) == 0

    def test_contains(self):
        cid = CaseInsensitiveDict()
        cid["Spam"] = "someval"
        assert "Spam" in cid
        assert "spam" in cid
        assert "SPAM" in cid
        assert "sPam" in cid
        assert "notspam" not in cid

    def test_get(self):
        cid = CaseInsensitiveDict()
        cid["spam"] = "oneval"
        cid["SPAM"] = "blueval"
        assert cid.get("spam") == "blueval"
        assert cid.get("SPAM") == "blueval"
        assert cid.get("sPam") == "blueval"
        assert cid.get("notspam", "default") == "default"

    def test_update(self):
        cid = CaseInsensitiveDict()
        cid["spam"] = "blueval"
        cid.update({"sPam": "notblueval"})
        assert cid["spam"] == "notblueval"
        cid = CaseInsensitiveDict({"Foo": "foo", "BAr": "bar"})
        cid.update({"fOO": "anotherfoo", "bAR": "anotherbar"})
        assert len(cid) == 2
        assert cid["foo"] == "anotherfoo"
        assert cid["bar"] == "anotherbar"

    def test_update_retains_unchanged(self):
        cid = CaseInsensitiveDict({"foo": "foo", "bar": "bar"})
        cid.update({"foo": "newfoo"})
        assert cid["bar"] == "bar"

    def test_iter(self):
        cid = CaseInsensitiveDict({"Spam": "spam", "Eggs": "eggs"})
        keys = frozenset(["Spam", "Eggs"])
        assert frozenset(iter(cid)) == keys

    def test_equality(self):
        cid = CaseInsensitiveDict({"SPAM": "blueval", "Eggs": "redval"})
        othercid = CaseInsensitiveDict({"spam": "blueval", "eggs": "redval"})
        assert cid == othercid
        del othercid["spam"]
        assert cid != othercid
        assert cid == {"spam": "blueval", "eggs": "redval"}
        assert cid != object()

    def test_setdefault(self):
        cid = CaseInsensitiveDict({"Spam": "blueval"})
        assert cid.setdefault("spam", "notblueval") == "blueval"
        assert cid.setdefault("notspam", "notblueval") == "notblueval"

    def test_lower_items(self):
        cid = CaseInsensitiveDict(
            {
                "Accept": "application/json",
                "user-Agent": "requests",
            }
        )
        keyset = frozenset(lowerkey for lowerkey, v in cid.lower_items())
        lowerkeyset = frozenset(["accept", "user-agent"])
        assert keyset == lowerkeyset

    def test_preserve_key_case(self):
        cid = CaseInsensitiveDict(
            {
                "Accept": "application/json",
                "user-Agent": "requests",
            }
        )
        keyset = frozenset(["Accept", "user-Agent"])
        assert frozenset(i[0] for i in cid.items()) == keyset
        assert frozenset(cid.keys()) == keyset
        assert frozenset(cid) == keyset

    def test_preserve_last_key_case(self):
        cid = CaseInsensitiveDict(
            {
                "Accept": "application/json",
                "user-Agent": "requests",
            }
        )
        cid.update({"ACCEPT": "application/json"})
        cid["USER-AGENT"] = "requests"
        keyset = frozenset(["ACCEPT", "USER-AGENT"])
        assert frozenset(i[0] for i in cid.items()) == keyset
        assert frozenset(cid.keys()) == keyset
        assert frozenset(cid) == keyset

    def test_copy(self):
        cid = CaseInsensitiveDict(
            {
                "Accept": "application/json",
                "user-Agent": "requests",
            }
        )
        cid_copy = cid.copy()
        assert str(cid) == str(cid_copy)
        assert cid == cid_copy
        cid["changed"] = True
        assert cid != cid_copy
