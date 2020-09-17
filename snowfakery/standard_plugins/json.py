import json
from typing import Union, Sequence, Mapping

from snowfakery.plugins import SnowfakeryPlugin, PluginResult, ArrayPluginResult


class JSONObject(Sequence, Mapping):
    __slots__ = ("value",)

    def __init__(self, value: Union[Sequence, Mapping]):
        self.value = value

    def sf_encode(self):
        return json.dumps(self.value, default=lambda x: x.__getstate__())

    def __getstate__(self):
        return self.value

    def __getitem__(self, index):
        return self.value[index]

    def __len__(self):
        return len(self.value)

    def __iter__(self):
        return iter(self.value)


class JSON(SnowfakeryPlugin):
    class Functions:
        def object(self, **kwargs):
            return PluginResult(JSONObject(kwargs))

        def array(self, *args):
            return ArrayPluginResult(JSONObject(args))
