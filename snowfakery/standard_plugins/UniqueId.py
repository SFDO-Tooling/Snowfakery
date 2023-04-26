import os
import time
from itertools import count
from math import log
import string

from baseconv import BaseConverter


from snowfakery import SnowfakeryPlugin
from snowfakery.plugins import PluginResult, PluginOption
from snowfakery import data_gen_exceptions as exc

from snowfakery.utils.scrambled_numbers import scramble_number

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
            UniqueId.NumericIdGenerator: index
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
            UniqueId.NumericIdGenerator: pid, index

You can also ask the algorithm to "mix in" a number you specify yourself:

        - plugin: snowfakery.standard_plugins.UniqueId
        - var: MyGenerator1
          value:
            UniqueId.NumericIdGenerator: 11, pid, index

Or based on a variable or recipe option:

        - plugin: snowfakery.standard_plugins.UniqueId
        - option: computer_number
        - var: MyGenerator1
          value:
            UniqueId.NumericIdGenerator: ${{computer_number}}, pid, index

"""

### Implementation strategy
#
# Imagine that we want to treat a group of numbers like a hierarchical namespace
# Analogous to subomain.domain.tld or 127.99.0.1 or /directory/directory/directory
#
# In each of the examples above, we use a separator character. But we want our
# numbers to be integers with no obvious separators.
#
# Our trick: convert the numbers to octal and use "9" as the separator.
#
# So given these numbers: [127, 99, 0, 1] we can do this:
#
# >>> lst = [127, 99, 0, 1]
# >>> octnums = [oct(x) for x in lst]
# >>> octnums
# ['0o177', '0o143', '0o0', '0o1']
# >>> as_str = "9".join(octnum[2:] for octnum in octnums)
# >>> as_str
# '17791439091'
#
# This is a unique and reversible representation of that list of numbers.
#
# Note that the number "8" and the string "99" will never appear in these
# numbers, so they are a subset of the normal integers.
#
# TODO: Benchmark Cantor Tuples instead.


def _oct(number):
    return oct(number)[2:]


class UniqueNumericIdGenerator(PluginResult):
    context_uniqifier = count(1)

    def __init__(
        self,
        *,
        parts: str,
        pid: int = None,
        min_chars: int = None,
        randomize: bool = True,
        start: int = 1,
    ):
        self.unique_identifer = next(self.context_uniqifier)
        self.counter = count(start)
        self.start = start
        self.parts = parts
        self.pid = self._get_pid(pid)
        parts = [self._convert(part.strip().lower()) for part in parts.split(",")]
        self.number_template = "9".join(parts)
        self.min_chars = min_chars
        self.result = {}  # implementation detail of PluginResults
        self.randomize = randomize

    def _get_pid(self, pid) -> str:
        if isinstance(pid, int):
            return _oct(pid)
        elif pid is not None:  # pragma: no cover
            assert type(pid) in (
                int,
                type(None),
            ), f"Unsupported datatype for pid: {pid}"

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
        # possible future feature: rand8, rand16, etc.
        # elif part.startswith("rand"):
        #     # note that rand is only evaluated once per generator! Not for every generation
        #     numbits = int(part[4:])
        #     return _oct(random.getrandbits(numbits))
        elif part.isnumeric() or isinstance(part, int):
            return _oct(int(part))
        elif part == "index":
            return "{index:o}"
        elif part == "context":
            return _oct(self.unique_identifer)
        else:
            raise exc.DataGenValueError(f"Unknown input to eval: {part}")

    @property
    def unique_id(self) -> int:
        index = next(self.counter)
        val = self.number_template.format(index=index)
        if self.randomize:
            return scramble_number(int(val))
        else:
            return int(val)

    def __reduce__(self):
        state = {
            # don't include pid: continuation processes shoud have their own.
            "parts": self.parts,
            "min_chars": self.min_chars,
            "randomize": self.randomize,
            "start": self.start,
        }
        return (
            self.__class__,
            (state,),
        )


class AlphaUniquifier(PluginResult):
    def __init__(
        self,
        *,
        pid: int = None,
        parts: str = None,
        alphabet: str = None,
        randomize_codes: bool = True,
        min_chars: int = 8,
    ):
        self.randomize_codes = randomize_codes

        # can't randomize extremely small numbers
        if randomize_codes:
            min_chars = max(min_chars, 4)
        self.number_generator = UniqueNumericIdGenerator(
            pid=pid, parts=parts, start=1001, randomize=False
        )
        self.alphabet = alphabet or string.digits + string.ascii_uppercase
        self.alpha_encoder = BaseConverter(self.alphabet).encode
        self.min_chars = min_chars
        self.result = {}  # implementation detail of PluginResults

    def _randomize_number(self, number: int):
        bits_per_char = int(log(len(self.alphabet), 2))
        min_bits = int(self.min_chars) * bits_per_char
        return scramble_number(int(number), min_bits)

    @property
    def unique_id(self) -> str:
        next_number = int(self.number_generator.unique_id)
        if self.randomize_codes:
            next_number = self._randomize_number(next_number)
        return self.alpha_encoder(next_number).rjust(self.min_chars, self.alphabet[0])


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
        _default_unique_id_generator = None
        _default_unique_alpha_code_generator = None

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
            if not self._default_unique_id_generator:
                self._default_unique_id_generator = self.NumericIdGenerator()
            return self._default_unique_id_generator

        @property
        def default_alpha_code_generator(self):
            if not self._default_unique_alpha_code_generator:
                self._default_unique_alpha_code_generator = self.AlphaCodeGenerator()
            return self._default_unique_alpha_code_generator

        @property
        def unique_id(self):
            return self.default_uniqifier.unique_id

        def NumericIdGenerator(self, _=None, *, template: str = None):
            template = template or (
                "pid,context,index" if self._bigids else "context,index"
            )
            return UniqueNumericIdGenerator(pid=self._pid, parts=template)

        def AlphaCodeGenerator(
            self,
            template=None,
            alphabet=None,
            min_chars: int = 8,
            randomize_codes: bool = True,
        ):
            alphabet = str(alphabet) if isinstance(alphabet, int) else alphabet
            template = template or ("pid,context,index" if self._bigids else "index")

            return AlphaUniquifier(
                pid=self._pid,
                parts=template,
                alphabet=alphabet,
                min_chars=min_chars,
                randomize_codes=randomize_codes,
            )
