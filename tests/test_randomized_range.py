from unittest.mock import patch

from snowfakery.utils.randomized_range import random_range, UpdatableRandomRange


class TestRandomizedRange:
    @patch("random.randint", return_value=11)
    def test_randomized_range(self, randint):
        rr = list(random_range(0, 10))
        assert rr != list(range(0, 10))
        assert sorted(rr) == list(range(0, 10))


@patch("random.randint", return_value=11)
class TestUpdatableRandomRange:
    def test_randomized_range(self, randint):
        urr = UpdatableRandomRange(0, 10)
        values = tuple(urr)
        assert sorted(values) == list(range(0, 10))
        assert values != list(range(0, 10))

        urr.set_new_range(10, 25)
        values = tuple(urr)
        assert sorted(values) == list(range(10, 25))
        assert values != list(range(10, 25))

    def test_randomized_range__non_overlapping(self, randint):
        urr = UpdatableRandomRange(3, 10)
        values = (next(urr), next(urr))

        assert values[0] != values[1]
        for val in values:
            assert 3 <= val < 10

        urr.set_new_range(10, 17)

        values = (next(urr), next(urr))

        assert values[0] != values[1]
        for val in values:
            assert 10 <= val < 17
        rest = tuple(urr)
        assert sorted(values + rest) == list(range(10, 17))

    def test_randomized_range__overlapping(self, randint):
        urr = UpdatableRandomRange(3, 10)
        values = (next(urr), next(urr))

        assert values[0] != values[1]
        for val in values:
            assert 3 <= val < 10
        urr.set_new_range(3, 12)
        urr.set_new_range(3, 14)
        middle_values = (next(urr), next(urr))
        for val in middle_values:
            assert 3 <= val < 14
        urr.set_new_range(3, 20)
        rest = tuple(urr)
        assert sorted(values + middle_values + rest) == list(range(3, 20))
