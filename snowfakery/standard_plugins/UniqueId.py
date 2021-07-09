from snowfakery import SnowfakeryPlugin
from snowfakery.plugins import PluginResult, PluginOption

import os
import time
from itertools import count
import typing as T
import random

# the option name that the user specifies on the CLI or API is just "pid"
# but using this long name internally prevents us from clashing with the
# user's variable names.
plugin_option_pid = "snowfakery.standard_plugins.UniqueId.UniqueId.pid"
plugin_option_big_ids = "snowfakery.standard_plugins.UniqueId.UniqueId.big_ids"

"""
 == UniqueID Plugin ==

Simplest possible usage is like this:

        - plugin: snowfakery.standard_plugins.UniqueId
        - object: Example
          count: 2
          fields:
            unique: ${{UniqueId.unique_id}}

You will get a roughly 17 character identifier. This identifier
incorporates something called the `current portion identifier` and
a per-element index.

You can create your own, custom unique value generator using a
"generator template":

        - plugin: snowfakery.standard_plugins.UniqueId
        - var: MyGenerator
          value:
            UniqueId.Generator: index
        - object: Example
          count: 2
          fields:
            unique: ${{MyGenerator.unique_id}}

`index` in that example serves as the "template" for the generator.

This particular template will generate very small identifiers because it
does not attempt to generate values that will be unique across
processes running at the same time, or across multiple loads. It just
uses a local index that starts as a single digit and grows.

The default template incorporates something called a "portion identifier"
along with the index. The portion identifier essentially guarantees
uniqueness even if the recipe is run on two different computers
or on the same computer at two different times of day. If you wanted to
include the portion identifer yourself (as the default template does),
you would use this template:

        - plugin: snowfakery.standard_plugins.UniqueId
        - var: MyGenerator1
          value:
            UniqueId.Generator: pid, index

You can also ask the algorithm to "mix in" a number you specify yourself:

        - plugin: snowfakery.standard_plugins.UniqueId
        - var: MyGenerator1
          value:
            UniqueId.Generator: 11, pid, index

Or based on a variable or recipe option:

        - plugin: snowfakery.standard_plugins.UniqueId
        - option: computer_number
        - var: MyGenerator1
          value:
            UniqueId.Generator: ${{computer_number}}, pid, index

"""


def _oct(number):
    print(number)
    return oct(number)[2:]


class Uniqifier(PluginResult):
    def __init__(self, pid: T.Union[int, str] = None, parts: str = None):
        print("YYY", pid, type(pid))
        if isinstance(pid, str):
            self.pid = _oct(int(pid))
        elif isinstance(pid, int):
            self.pid = _oct(pid)
        elif pid is None:
            self.pid = self._default_pid()
        parts = [self._convert(part.strip().lower()) for part in parts.split(",")]
        self.template = "9".join(parts)
        self.counter = count(1)

    def _default_pid(self):
        return (
            _oct(int(time.time() - time.mktime((2021, 1, 1, 0, 0, 0, 0, 0, 0))))
            + "9"
            + _oct(os.getpid())
        )

    def _convert(self, part):
        if isinstance(part, str):
            part = part.lower()
        if part == "pid":
            return self.pid
        elif part.startswith("rand"):
            numbits = int(part[4:])
            return _oct(random.getrandbits(numbits))
        elif isinstance(part, int):
            return _oct(part)
        elif part.isnumeric():
            return _oct(int(part))
        elif part == "index":
            return "{index:o}"
        else:
            assert False, f"Unknown input to eval: {part}"  # FIXME

    @property
    def unique_id(self):
        return self.template.format(index=next(self.counter))


def as_bool(opt):
    if isinstance(opt, str) and opt.lower() in ["true", "1", "yes"]:
        return True
    elif isinstance(opt, str) and opt.lower() in ["false", "0", "no"]:
        return False
    elif isinstance(opt, int):
        return bool(opt)
    else:
        raise TypeError(opt)


class UniqueId(SnowfakeryPlugin):
    allowed_options = [
        PluginOption(plugin_option_pid, int),
        PluginOption(plugin_option_big_ids, as_bool),
    ]

    class Functions:
        _default_uniqifier = None

        @property
        def _pid(self):
            fieldvars = self.context.field_vars()
            return fieldvars.get(plugin_option_pid)

        @property
        def _bigids(self):
            fieldvars = self.context.field_vars()
            return fieldvars.get(plugin_option_big_ids)

        @property
        def default_uniqifier(self):
            if not self._default_uniqifier:
                template = "pid,rand8,index" if self._bigids else "index"
                self._default_uniqifier = Uniqifier(self._pid, template)
            return self._default_uniqifier

        @property
        def unique_id(self):
            return self.default_uniqifier.unique_id

        def Generator(self, parts=None):
            parts = parts or "index"
            return Uniqifier(self._pid, parts)
