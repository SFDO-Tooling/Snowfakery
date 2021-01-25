import importlib.util

from snowfakery.plugins import SnowfakeryPlugin


class Math(SnowfakeryPlugin):
    def custom_functions(self, *args, **kwargs):
        "Expose math functions to Snowfakery"
        mathmodule = importlib.util.find_spec("math")
        math = importlib.util.module_from_spec(mathmodule)

        math.round = round
        math.min = min
        math.max = max

        return math
