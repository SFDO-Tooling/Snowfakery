from random import Random
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
SHIFT2 = 10 ** 2
SHIFT3 = 10 ** 3


def scramble_number(number: int, minbits: int = 0) -> int:
    "Make a number that looks random"

    minbits = max(8, minbits - 9)  # I'm going to add about 9 bits at the end :(
    key = number % SHIFT1  # last digit (or bits) is a randomization key
    # remove the key from the number
    number = number // SHIFT1
    # how many bits I need to fiddle with
    numbits = max(minbits, int(log(number, 2)) + 1)
    assert numbits < SHIFT2
    # make a randomized mask based on the key
    mask = mask_for_key(key, numbits)
    # make the number look random by applying the mask
    scrambled = mask ^ number
    # return the number, the key and the number of bits that can reverse the scrambling
    return scrambled * SHIFT3 + key * SHIFT2 + numbits


def unscramble_number(number):
    numbits = number % SHIFT2
    number = number - numbits
    key = (number % SHIFT3) / SHIFT2
    number = (number - key * SHIFT2) / SHIFT3
    mask = mask_for_key(key, numbits)
    return int(number) + key ^ mask
