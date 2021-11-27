from snowfakery import SnowfakeryPlugin


class DoublingPlugin(SnowfakeryPlugin):
    class Functions:
        def double(self, value):
            return value * 2
