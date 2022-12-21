import math
from random import randint, shuffle
from types import SimpleNamespace
from typing import List, Optional, Union
from snowfakery.plugins import SnowfakeryPlugin, memorable, PluginResultIterator


class Math(SnowfakeryPlugin):
    def custom_functions(self, *args, **kwargs):
        "Expose math functions to Snowfakery"

        class MathNamespace(SimpleNamespace):
            @memorable
            def random_partition(
                self,
                total: int,
                *,
                min: int = 1,
                max: Optional[int] = None,
                step: int = 1,
            ):
                return GenericPluginResultIterator(False, parts(total, min, max, step))

        mathns = MathNamespace()
        mathns.__dict__.update(math.__dict__.copy())

        mathns.pi = math.pi
        mathns.round = round
        mathns.min = min
        mathns.max = max
        mathns.context = self.context
        return mathns


class GenericPluginResultIterator(PluginResultIterator):
    def __init__(self, repeat, iterable):
        super().__init__(repeat)
        self.next = iter(iterable).__next__


def parts(total: int, min_: int = 1, max_=None, step=1) -> List[Union[int, float]]:
    """Split a number into a randomized set of 'pieces'.
    The pieces add up to the `total`. E.g.

    parts(12) -> [3, 6, 3]
    parts(16) -> [8, 4, 2, 2]

    The numbers generated will never be less than `min_`, if provided.

    The numbers generated will never be less than `max_`, if provided.

    The numbers generated will always be a multiple of `step`, if provided.

    But...if you provide inconsistent constraints then your values
    will be inconsistent with them. e.g. if `total` is not a multiple
    of `step`.
    """
    max_ = max_ or total
    factor = 0

    if step < 1:
        assert step in [0.01, 0.5, 0.1, 0.20, 0.25, 0.50], step
        factor = step
        total = int(total / factor)
        step = int(total / factor)
        min_ = int(total / factor)
        max_ = int(total / factor)

    pieces = []

    while sum(pieces) < total:
        remaining = total - sum(pieces)
        smallest = max(min_, step)
        if remaining < smallest:
            # try to add it to a random other piece
            for i, val in enumerate(pieces):
                if val + remaining <= max_:
                    pieces[i] += remaining
                    remaining = 0
                    break

            # just tack it on the end despite
            # it being too small...our
            # constraints must have been impossible
            # to fulfil
            if remaining:
                pieces.append(remaining)

        else:
            part = randint(smallest, min(remaining, max_))
            round_up = part + step - (part % step)
            if round_up <= min(remaining, max_) and randint(0, 1):
                part = round_up
            else:
                part -= part % step

            pieces.append(part)

    assert sum(pieces) == total, pieces
    assert 0 not in pieces, pieces

    shuffle(pieces)
    if factor:
        pieces = [round(p * factor, 2) for p in pieces]
    return pieces
