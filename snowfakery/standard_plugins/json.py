import json
from typing import Union, Sequence, Mapping
from contextlib import contextmanager

from snowfakery.data_generator_runtime import ObjectRow
from snowfakery.plugins import SnowfakeryPlugin, PluginResult, lazy, ArrayPluginResult


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


@contextmanager
def fake_object_row(c):
    """Make a fake object row as part of evaluation context

    Some plugins expect to be executed in the context of an object row"""
    mydata = {"id": "None"}  # fake
    c.obj = ObjectRow("", mydata)
    yield mydata

    # clean up id because json objects don't have an id
    del mydata["id"]
    for k in mydata.keys():
        if k.startswith("__"):
            del mydata[k]


class JSON(SnowfakeryPlugin):
    class Functions:
        @lazy
        def object(self, **kwargs):
            with self.context.interpreter.current_context.child_context(None) as c:
                with fake_object_row(c) as mydata:
                    for k, v in kwargs.items():
                        mydata[k] = self.context.evaluate(v)
                    return PluginResult(JSONObject(mydata))

        @lazy
        def array(self, *args):
            with self.context.interpreter.current_context.child_context(None) as c:
                with fake_object_row(c):
                    children = [self.context.evaluate(arg) for arg in args]

                return ArrayPluginResult(JSONObject(children))
