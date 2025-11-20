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
from snowfakery.utils.validation_utils import resolve_value

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

    class Validators:
        """Validators for UniqueId plugin functions."""

        @staticmethod
        def validate_NumericIdGenerator(sv, context):
            """Validate UniqueId.NumericIdGenerator(template=None)

            Args:
                sv: StructuredValue with args/kwargs
                context: ValidationContext for error reporting
            """
            kwargs = getattr(sv, "kwargs", {})
            args = getattr(sv, "args", [])

            # Get template value (can be positional or keyword)
            template = None
            if args:
                template = args[0]
            elif "template" in kwargs:
                template = kwargs["template"]

            # Validate template if provided
            if template is not None:
                template_val = resolve_value(template, context)

                if template_val is not None:
                    # ERROR: Template must be string
                    if not isinstance(template_val, str):
                        context.add_error(
                            f"UniqueId.NumericIdGenerator: 'template' must be a string, got {type(template_val).__name__}",
                            getattr(sv, "filename", None),
                            getattr(sv, "line_num", None),
                        )
                        # Return mock generator object even on error
                        return type(
                            "MockNumericGenerator", (), {"unique_id": 1234567890}
                        )()

                    # Validate template parts
                    valid_parts = {"pid", "context", "index"}
                    parts = [p.strip().lower() for p in template_val.split(",")]

                    for part in parts:
                        # Check if it's numeric
                        if part.isnumeric():
                            continue

                        # Check if it's a valid part
                        if part not in valid_parts:
                            context.add_error(
                                f"UniqueId.NumericIdGenerator: Invalid template part '{part}'. "
                                f"Valid parts: {', '.join(sorted(valid_parts))}, or numeric values",
                                getattr(sv, "filename", None),
                                getattr(sv, "line_num", None),
                            )

            # WARNING: Unknown parameters
            valid_params = {"template", "_"}
            unknown = set(kwargs.keys()) - valid_params
            if unknown:
                context.add_warning(
                    f"UniqueId.NumericIdGenerator: Unknown parameter(s): {', '.join(unknown)}",
                    getattr(sv, "filename", None),
                    getattr(sv, "line_num", None),
                )

            # Return intelligent mock: mock generator object with unique_id property
            return type("MockNumericGenerator", (), {"unique_id": 1234567890})()

        @staticmethod
        def validate_AlphaCodeGenerator(sv, context):
            """Validate UniqueId.AlphaCodeGenerator(template, alphabet, min_chars, randomize_codes)

            Args:
                sv: StructuredValue with args/kwargs
                context: ValidationContext for error reporting
            """
            kwargs = getattr(sv, "kwargs", {})

            # Validate template (same as NumericIdGenerator)
            if "template" in kwargs:
                template_val = resolve_value(kwargs["template"], context)

                if template_val is not None and isinstance(template_val, str):
                    valid_parts = {"pid", "context", "index"}
                    parts = [p.strip().lower() for p in template_val.split(",")]

                    for part in parts:
                        if not part.isnumeric() and part not in valid_parts:
                            context.add_error(
                                f"UniqueId.AlphaCodeGenerator: Invalid template part '{part}'. "
                                f"Valid parts: {', '.join(sorted(valid_parts))}, or numeric values",
                                getattr(sv, "filename", None),
                                getattr(sv, "line_num", None),
                            )

            # Validate alphabet
            if "alphabet" in kwargs:
                alphabet_val = resolve_value(kwargs["alphabet"], context)

                if alphabet_val is not None:
                    # ERROR: Must be string
                    if not isinstance(alphabet_val, str):
                        context.add_error(
                            f"UniqueId.AlphaCodeGenerator: 'alphabet' must be a string, got {type(alphabet_val).__name__}",
                            getattr(sv, "filename", None),
                            getattr(sv, "line_num", None),
                        )
                    # ERROR: Must have at least 2 characters
                    elif len(alphabet_val) < 2:
                        context.add_error(
                            "UniqueId.AlphaCodeGenerator: 'alphabet' must have at least 2 characters",
                            getattr(sv, "filename", None),
                            getattr(sv, "line_num", None),
                        )
                    else:
                        # Check if alphabet is large enough for randomization
                        # When randomize_codes=True, we need at least 10 bits
                        # bits_per_char = log2(len(alphabet))
                        # For min_chars=4 (the minimum when randomize_codes=True):
                        # We need: 4 * log2(len(alphabet)) >= 10
                        # So: log2(len(alphabet)) >= 2.5
                        # So: len(alphabet) >= 2^2.5 ≈ 5.66, meaning at least 6 characters

                        # Get randomize_codes value (default is True)
                        randomize_codes = True
                        if "randomize_codes" in kwargs:
                            randomize_val = resolve_value(
                                kwargs["randomize_codes"], context
                            )
                            if randomize_val is not None and isinstance(
                                randomize_val, bool
                            ):
                                randomize_codes = randomize_val

                        # Get min_chars value (default is 8, but becomes 4 if randomize_codes=True)
                        min_chars = 8
                        if "min_chars" in kwargs:
                            min_chars_val = resolve_value(kwargs["min_chars"], context)
                            if min_chars_val is not None and isinstance(
                                min_chars_val, int
                            ):
                                min_chars = min_chars_val

                        if randomize_codes:
                            # When randomizing, min_chars is at least 4
                            effective_min_chars = max(min_chars, 4)
                            bits_per_char = int(log(len(alphabet_val), 2))
                            min_bits = effective_min_chars * bits_per_char

                            # ERROR: Alphabet too small for randomization
                            if min_bits < 10:
                                context.add_error(
                                    f"UniqueId.AlphaCodeGenerator: 'alphabet' with {len(alphabet_val)} characters is too small for randomization. "
                                    f"With min_chars={effective_min_chars}, this gives {min_bits} bits but requires at least 10 bits. "
                                    f"Use an alphabet with at least 6 characters, or set randomize_codes=False",
                                    getattr(sv, "filename", None),
                                    getattr(sv, "line_num", None),
                                )

            # Validate min_chars
            if "min_chars" in kwargs:
                min_chars_val = resolve_value(kwargs["min_chars"], context)

                if min_chars_val is not None:
                    # ERROR: Must be integer
                    if not isinstance(min_chars_val, int):
                        context.add_error(
                            f"UniqueId.AlphaCodeGenerator: 'min_chars' must be an integer, got {type(min_chars_val).__name__}",
                            getattr(sv, "filename", None),
                            getattr(sv, "line_num", None),
                        )
                    # ERROR: Must be positive
                    elif min_chars_val <= 0:
                        context.add_error(
                            "UniqueId.AlphaCodeGenerator: 'min_chars' must be positive",
                            getattr(sv, "filename", None),
                            getattr(sv, "line_num", None),
                        )

            # Validate randomize_codes
            if "randomize_codes" in kwargs:
                randomize_val = resolve_value(kwargs["randomize_codes"], context)

                if randomize_val is not None and not isinstance(randomize_val, bool):
                    context.add_error(
                        f"UniqueId.AlphaCodeGenerator: 'randomize_codes' must be a boolean, got {type(randomize_val).__name__}",
                        getattr(sv, "filename", None),
                        getattr(sv, "line_num", None),
                    )

            # WARNING: Unknown parameters
            valid_params = {"template", "alphabet", "min_chars", "randomize_codes"}
            unknown = set(kwargs.keys()) - valid_params
            if unknown:
                context.add_warning(
                    f"UniqueId.AlphaCodeGenerator: Unknown parameter(s): {', '.join(unknown)}",
                    getattr(sv, "filename", None),
                    getattr(sv, "line_num", None),
                )

            # Return intelligent mock: alpha code generator object
            min_chars = 8  # Default
            if "min_chars" in kwargs:
                min_chars_val = resolve_value(kwargs["min_chars"], context)
                if isinstance(min_chars_val, int) and min_chars_val > 0:
                    min_chars = min_chars_val

            # Get alphabet if provided
            alphabet = None
            if "alphabet" in kwargs:
                alphabet_val = resolve_value(kwargs["alphabet"], context)
                if isinstance(alphabet_val, str) and len(alphabet_val) >= 2:
                    alphabet = alphabet_val

            # Generate mock alpha code
            if alphabet:
                # Use first character from alphabet repeated to min_chars length
                mock_code = alphabet[0] * min_chars
            else:
                # Default: use 'A' repeated to min_chars length
                mock_code = "A" * min_chars

            # Return mock generator object with unique_id property
            return type("MockAlphaGenerator", (), {"unique_id": mock_code})()
