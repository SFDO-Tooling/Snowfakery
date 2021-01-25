from random import randint, shuffle

from snowfakery.plugins import SnowfakeryPlugin, PluginResult


def parts(total, step):
    assert total % step == 0
    pieces = []

    while sum(pieces) < total:
        top = (total - sum(pieces)) / step
        pieces.append(randint(1, top) * step)

    shuffle(pieces)
    return pieces


class Summation(PluginResult):
    def __init__(self, total, step):
        self.total = total
        self.pieces = parts(total, step)
        self.running_total = 0
        super().__init__(None)

    @property
    def count(self, null=None):
        return len(self.pieces)

    @property
    def next_amount(self):
        rc = self.pieces.pop()
        self.running_total += rc
        return rc


class SummationPlugin(SnowfakeryPlugin):
    class Functions:
        def summer(self, total, step):
            return Summation(total, step)
