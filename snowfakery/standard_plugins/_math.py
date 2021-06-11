import math
from snowfakery.plugins import SnowfakeryPlugin


class Math(SnowfakeryPlugin):
    def custom_functions(self, *args, **kwargs):
        "Expose math functions to Snowfakery"

        class MathNamespace:
            pass

        mathns = MathNamespace()
        mathns.__dict__ = math.__dict__.copy()

        mathns.pi = math.pi
        mathns.round = round
        mathns.min = min
        mathns.max = max

        return mathns
