from snowfakery.data_generator_runtime import ObjectRow, NicknameSlot


class TestObjectRow:
    def test_repr(self):
        "Test repr handles even invalid objects, for debugging"
        obj = ObjectRow("A", {"id": "5", "b": "c"})
        assert repr(obj)
        called = False

        class ProblemValue:
            def __repr__(self):
                nonlocal called
                called = True
                raise Exception()

        obj = ObjectRow(ProblemValue(), {"id": ProblemValue()})
        assert repr(obj)
        assert called

        obj = ObjectRow("", {})
        assert repr(obj)


class TestNicknameSlot:
    def test_nickname_slot(self):
        n = NicknameSlot("Foo", None)
        repr(n)
        str(n)
