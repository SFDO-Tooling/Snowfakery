import math
from random import Random
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
                step: float = 1,
            ):
                random = self.context.random_number_generator
                return GenericPluginResultIterator(
                    False, parts(total, min, max, step, random)
                )

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


def parts(
    total: int,
    min_: int = 1,
    max_: Optional[int] = None,
    requested_step: float = 1,
    rand: Optional[Random] = None,
) -> List[Union[int, float]]:
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
    rand = rand or Random()

    if requested_step < 1:
        allowed_steps = [0.01, 0.5, 0.1, 0.20, 0.25, 0.50]
        assert (
            requested_step in allowed_steps
        ), f"`step` must be one of {', '.join(str(f) for f in allowed_steps)}, not {requested_step}"
        # multiply up into the integer range so we don't need to do float math
        total = int(total / requested_step)
        step = 1
        min_ = int(min_ / requested_step)
        max_ = int(max_ / requested_step)
    else:
        step = int(requested_step)
        assert step == requested_step, f"`step` should be an integer, not {step}"

    pieces = []

    while sum(pieces) < total:
        remaining = total - sum(pieces)
        smallest = max(min_, step)
        if remaining < smallest:
            # mutates pieces
            handle_last_bit(pieces, rand, remaining, min_, max_)

        else:
            pieces.append(generate_piece(pieces, rand, smallest, remaining, max_, step))

    assert sum(pieces) == total, pieces
    assert 0 not in pieces, pieces

    if requested_step != step:
        pieces = [round(p * requested_step, 2) for p in pieces]
    return pieces


def handle_last_bit(
    pieces: List[int], rand: Random, remaining: int, min_: int, max_: int
):
    """If the piece is big enough, add it.
    Otherwise, try to add it to another piece."""

    if remaining > min_:
        pos = rand.randint(0, len(pieces))
        pieces.insert(pos, remaining)
        return

    # try to add it to some other piece
    for i, val in enumerate(pieces):
        if val + remaining <= max_:
            pieces[i] += remaining
            remaining = 0
            return

    # just insert it despite it being too small...our
    # constraints must have been impossible to fulfill
    if remaining:
        pos = rand.randint(0, len(pieces))
        pieces.insert(pos, remaining)


def generate_piece(
    pieces: List[int], rand: Random, smallest: int, remaining: int, max_: int, step: int
):
    part = rand.randint(smallest, min(remaining, max_))
    round_up = part + step - (part % step)
    if round_up <= min(remaining, max_) and rand.randint(0, 1):
        part = round_up
    else:
        part -= part % step

    return part
