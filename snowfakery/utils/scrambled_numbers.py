from random import Random, randint
from copy import copy
from math import log
from functools import lru_cache


@lru_cache()
def randomizer(key):
    return Random(key)


@lru_cache()
def mask_for_key(key, numbits):
    r = copy(randomizer(key))
    return r.getrandbits(numbits)


SHIFT1 = 10
SHIFT2 = SHIFT1 * 100
SHIFT3 = SHIFT2 * SHIFT1


def scramble_number(number: int, minbits: int = 10) -> int:
    "Make a number that looks random"

    assert minbits >= 10

    minbits = max(10, minbits - 13)  # I'm going to add about 13 bits at the end :(
    key = number % SHIFT1  # last digit (or bits) is a randomization key
    # remove the key from the number
    number = number // SHIFT1
    # how many bits I need to fiddle with
    numbits = max(minbits, (int(log(number, 2)) + 1) if number else minbits)
    assert numbits < SHIFT2
    # make a randomized mask based on the key
    mask = mask_for_key(key, numbits)
    # make the number look random by applying the mask
    scrambled = number ^ mask
    # return the number, the key and the number of bits that can reverse the scrambling
    return scrambled * SHIFT3 + key * SHIFT2 + numbits


def unscramble_number(number):
    # extract the numbits (least significant digits)
    numbits = number % SHIFT2
    # clear them out
    number = number - numbits
    # extract the key (next least significant)
    key = int((number % SHIFT3) / SHIFT2)
    # clear them out
    number = number - (key * SHIFT2)
    assert number % SHIFT3 == 0
    scrambled = number // SHIFT3
    # find the right mask
    mask = mask_for_key(key, numbits)
    unscrambled = scrambled ^ mask
    # put the key back
    return unscrambled * SHIFT1 + key


# If a function can be undone, then it is bijective
# i.e. each output has ONLY ONE input
def _test_scrambling_is_safe(iterations):
    for _ in range(0, iterations):
        for numsize in range(5, 100):
            for minbits in range(10, 100):
                num = randint(10, 10 ** numsize)
                scrambled = scramble_number(num, minbits)
                unscrambled = unscramble_number(scrambled)
                assert unscrambled == num, (num, minbits, scrambled)


if __name__ == "__main__":  # pragma: no cover
    _test_scrambling_is_safe(50)
