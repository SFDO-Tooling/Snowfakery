from random import randint, shuffle

from snowfakery.plugins import SnowfakeryPlugin, PluginResult


def parts(total, step):
    """Split a number into a randomized set of 'pieces'.
    The pieces add up to the number. E.g.

    parts(12, 3) -> [3, 6, 3]
    parts(16, 4) -> [8, 4, 4]

    >>> assert len(parts(12, 3)) > 1
    >>> assert sum(parts(12, 3)) == 12
    """
    assert total % step == 0
    pieces = []

    while sum(pieces) < total:
        top = (total - sum(pieces)) / step
        pieces.append(randint(1, top) * step)

    shuffle(pieces)
    return pieces


class Summation(PluginResult):
    """Represent a group of pieces"""

    def __init__(self, total, step):
        self.total = total
        self.pieces = parts(total, step)
        super().__init__(None)

    @property
    def count(self, null=None):
        return len(self.pieces)

    @property
    def next_amount(self):
        rc = self.pieces.pop()
        return rc


class SummationPlugin(SnowfakeryPlugin):
    """Plugin which generates a summataion helper"""

    class Functions:
        def summer(self, total, step):
            return Summation(total, step)
