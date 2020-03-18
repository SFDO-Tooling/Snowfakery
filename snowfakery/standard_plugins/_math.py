import math

from snowfakery.plugins import SnowfakeryPlugin


class Math(SnowfakeryPlugin):
    def custom_functions(self, *args, **kwargs):
        "Expose math functions to Snowfakery"
        return math
