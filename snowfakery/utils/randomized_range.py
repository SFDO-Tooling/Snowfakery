import typing as T
import random
import math


class UpdatableRandomRange:
    def __init__(self, start: int, stop: int = None):
        assert stop > start
        self.min = start
        self._set_new_range_immediately(start, stop)

    def set_new_max(self, new_max: int):
        # do not replace RNG until old one is exhausted
        assert new_max >= self.cur_max
        self.cur_max = new_max

    def set_new_range(self, new_min: int, new_max: int):
        """Update the range subject to constraints

        There are two modes:

        If you update the range by changing only the top value,
        the generator will finish generating the first list before
        expanding its scope.

        So if you configured it with range(0,10) and then
        range(0,20) you would get

        shuffle(list(range(0,10)) + shuffle(list(range(10,20))

        Not:

        shuffle(list(range(0,10) + list(range(10,20))

        If you update the range by changing both values, the previous
        generator is just discarded, because you presumably don't
        want those values anymore. The new bottom must be higher
        than the old top. This preserves the rule that no value is
        ever produced twice.
        """
        if new_min == self.min:
            self.set_new_max(new_max)
        else:
            assert new_min >= self.orig_max, (new_min, self.orig_max)
            self._set_new_range_immediately(new_min, new_max)

    def _set_new_range_immediately(self, new_min: int, new_max: int):
        assert new_max > new_min
        self.min = new_min
        self.orig_max = self.cur_max = new_max
        self.num_generator = random_range(self.min, self.orig_max)

    def __iter__(self):
        return self

    def __next__(self):
        rv = next(self.num_generator, None)

        if rv is not None:
            return rv

        if self.cur_max <= self.orig_max:
            raise StopIteration()

        self.min = self.orig_max
        self.num_generator = random_range(self.min, self.cur_max)
        self.orig_max = self.cur_max
        return next(self.num_generator)


def random_range(start: int, stop: int) -> T.Generator[int, None, None]:
    """
    Return a randomized "range" using a Linear Congruential Generator
    to produce the number sequence. Parameters are the same as for
    python builtin "range".
        Memory  -- storage for 8 integers, regardless of parameters.
        Compute -- at most 2*"maximum" steps required to generate sequence.
    Based on https://stackoverflow.com/a/53551417/113477

    # Set a default values the same way "range" does.
    """
    step = 1  # step is hard-coded to "1" because it seemed to be buggy
    # and not important for our use-case

    # Use a mapping to convert a standard range into the desired range.
    def mapping(i):
        return (i * step) + start

    # Compute the number of numbers in this range.
    maximum = (stop - start) // step

    # Seed range with a random integer.
    value = random.randint(0, maximum)
    #
    # Construct an offset, multiplier, and modulus for a linear
    # congruential generator. These generators are cyclic and
    # non-repeating when they maintain the properties:
    #
    #   1) "modulus" and "offset" are relatively prime.
    #   2) ["multiplier" - 1] is divisible by all prime factors of "modulus".
    #   3) ["multiplier" - 1] is divisible by 4 if "modulus" is divisible by 4.
    #
    offset = random.randint(0, maximum) * 2 + 1  # Pick a random odd-valued offset.
    multiplier = (
        4 * (maximum // 4) + 1
    )  # Pick a multiplier 1 greater than a multiple of 4.
    modulus = int(
        2 ** math.ceil(math.log2(maximum))
    )  # Pick a modulus just big enough to generate all numbers (power of 2).
    # Track how many random numbers have been returned.
    found = 0
    while found < maximum:
        # If this is a valid value, yield it in generator fashion.
        if value < maximum:
            found += 1
            yield mapping(value)
        # Calculate the next value in the sequence.
        value = (value * multiplier + offset) % modulus
