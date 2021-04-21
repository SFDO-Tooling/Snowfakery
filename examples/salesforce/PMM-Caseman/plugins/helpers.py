from snowfakery.plugins import SnowfakeryPlugin


class Helpers(SnowfakeryPlugin):
    class Functions:
        def round(self, number) -> int:
            """Round a number."""
            return round(number)
