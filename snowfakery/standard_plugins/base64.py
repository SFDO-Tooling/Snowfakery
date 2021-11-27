from base64 import b64encode
from snowfakery.plugins import SnowfakeryPlugin


class Base64(SnowfakeryPlugin):
    class Functions:
        def encode(self, data):
            return b64encode(bytes(str(data), "latin1")).decode("ascii")
