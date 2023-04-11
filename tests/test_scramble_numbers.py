from snowfakery.utils.scrambled_numbers import _test_scrambling_is_safe


class TestScrambleNumbers:
    def test_scramble(self):
        _test_scrambling_is_safe(1)
