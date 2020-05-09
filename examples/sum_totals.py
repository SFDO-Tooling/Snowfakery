from random import randint, shuffle, randrange

from snowfakery import SnowfakeryPlugin


def parts(total, step):
    assert total % step == 0
    pieces = []

    while sum(pieces) < total:
        top = (total - sum(pieces)) / step
        pieces.append(randint(1, top) * step)

    shuffle(pieces)
    return pieces


class Summation:
    def __init__(self, total, step):
        self.total = total
        self.pieces = parts(total, step)


class SummationPlugin(SnowfakeryPlugin):
    class Functions:
        def new_total(self, total, step):
            self.context.context_vars()["summation"] = Summation(total, step)
            return total

        def count(self, null=None):
            return len(self.context.context_vars()["summation"].pieces)

        def amount(self, null=None):
            summation = self.context.context_vars()["summation"]
            return summation.pieces.pop()

        def randrange(self, start, stop, step):
            return randrange(start, stop, step)
