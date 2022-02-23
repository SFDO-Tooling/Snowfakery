import sys
import random
from functools import lru_cache
from datetime import date, datetime
import dateutil.parser
import warnings
from dateutil.relativedelta import relativedelta
from ast import literal_eval

from typing import Union, List, Tuple, Any

from faker import Faker
from faker.providers.date_time import Provider as DateProvider

from .data_gen_exceptions import DataGenError

import snowfakery.data_generator_runtime  # noqa
from snowfakery.plugins import SnowfakeryPlugin, PluginContext, lazy
from snowfakery.object_rows import ObjectReference
from snowfakery.utils.template_utils import StringGenerator
from snowfakery.standard_plugins.UniqueId import UniqueId
from snowfakery.fakedata.fake_data_generator import UTCAsRelDelta, _normalize_timezone

FieldDefinition = "snowfakery.data_generator_runtime_object_model.FieldDefinition"

# It might make more sense to use context vars for context handling when
# Python 3.6 is out of the support matrix.


def parse_weight_str(context: PluginContext, weight_value) -> float:
    """For constructs like:

    - choice:
        probability: 60%
        pick: Closed Won

    Render and convert the 60% to just 60.
    """
    weight_str = context.evaluate(weight_value)
    if isinstance(weight_str, str):
        weight_str = weight_str.rstrip("%")
    return float(weight_str)


def weighted_choice(choices: List[Tuple[float, object]]):
    """Selects from choices based on their weights"""
    weights = [weight for weight, value in choices]
    options = [value for weight, value in choices]
    return random.choices(options, weights, k=1)[0]


@lru_cache(maxsize=512)
def parse_date(d: Union[str, datetime, date]) -> date:
    if isinstance(d, datetime):
        return d.date()
    elif isinstance(d, date):
        return d

    return dateutil.parser.parse(d).date()


def render_boolean(context: PluginContext, value: FieldDefinition) -> bool:
    val = context.evaluate(value)
    if isinstance(val, str):
        val = literal_eval(val)

    return bool(val)


class StandardFuncs(SnowfakeryPlugin):
    class Functions:
        int = int
        # use ONLY for random_dates
        # anything else should use the Faker from the Interpreter
        # which is locale-scoped.
        _faker_for_dates = Faker(use_weighting=False)
        _uidgen = None

        def __init__(self, *args, **kwargs):
            self.snowfakery_filename = StringGenerator(self._snowfakery_filename)
            self.unique_id = StringGenerator(self._unique_id)
            self.unique_alpha_code = StringGenerator(self._unique_alpha_code)

        def date(
            self,
            datespec=None,
            *,
            year: Union[str, int] = None,
            month: Union[str, int] = None,
            day: Union[str, int] = None,
        ):
            """A YAML-embeddable function to construct a date from strings or integers"""
            if datespec:
                return parse_date(datespec)
            else:
                return date(year, month, day)

        def datetime(
            self,
            *,
            year: Union[str, int],
            month: Union[str, int],
            day: Union[str, int],
            hour=0,
            minute=0,
            second=0,
            microsecond=0,
            timezone=UTCAsRelDelta,
        ):
            """A YAML-embeddable function to construct a datetime from strings or integers"""
            timezone = _normalize_timezone(timezone)
            return datetime(
                year, month, day, hour, minute, second, microsecond, tzinfo=timezone
            )

        def date_between(self, *, start_date, end_date):
            """A YAML-embeddable function to pick a date between two ranges"""

            def try_parse_date(d):
                if not isinstance(d, str) or not DateProvider.regex.fullmatch(d):
                    try:
                        d = parse_date(d)
                    except Exception:  # let's hope its something faker can parse
                        pass
                return d

            start_date = try_parse_date(start_date)
            end_date = try_parse_date(end_date)

            try:
                return self._faker_for_dates.date_between(start_date, end_date)
            except ValueError as e:
                if "empty range" not in str(e):
                    raise
            # swallow empty range errors per Python conventions

        def i18n_fake(self, locale: str, fake: str):
            # deprecated by still here for backwards compatibility
            faker = Faker(locale, use_weighting=False)
            func = getattr(faker, fake)
            return func()

        def random_number(self, min: int, max: int, step: int = 1) -> int:
            """Pick a random number between min and max like Python's randint."""
            return random.randrange(min, max + 1, step)

        def reference(
            self, x: Any = None, object: str = None, id: Union[str, int] = None
        ):
            """YAML-embeddable function to Reference another object."""
            if x is not None:
                return self._reference_from_scalar(x)
            elif object:
                try:
                    id = int(id)
                except TypeError:
                    raise DataGenError("Cannot interpret id as integer")
                return ObjectReference(object, id)

        def _reference_from_scalar(self, x: Any):
            if hasattr(x, "id"):  # reference to an object with an id
                target = x
            elif isinstance(x, str):  # name of an object
                # allows dotted paths
                parts = x.split(".")
                target = self.context.field_vars().get(parts.pop(0))

                for part in parts:
                    try:
                        target = getattr(target, part)
                    except AttributeError:
                        raise DataGenError(
                            f"Expression cannot be evaluated `{x}``. Problem before `{part}`:\n {target}",
                            None,
                            None,
                        )

                if not target:
                    raise DataGenError(f"Cannot find an object named {x}", None, None)
                if not getattr(target, "id", None):
                    raise DataGenError(
                        f"Reference to incorrect object type {target}", None, None
                    )
            else:
                raise DataGenError(
                    f"Can't get reference to object of type {type(x)}: {x}"
                )

            return target

        @lazy
        def random_choice(self, *choices, **kwchoices):
            """Template helper for random choices.

            Supports structures like this:

            random_choice:
                - a
                - b
                - ${{c}}

            Or like this:

            random_choice:
                - choice:
                    pick: A
                    probability: 50%
                - choice:
                    pick: A
                    probability: 50%

            Probabilities are really just weights and don't need to
            add up to 100.

            Pick-items can have arbitrary internal complexity.

            Pick-items are lazily evaluated.
            """

            # very occasionally single-item choices are useful
            use_choices = len(choices) >= 1

            # very occasionally single-item choices are useful
            use_kwchoices = len(kwchoices) >= 1

            if not (use_choices or use_kwchoices):
                raise ValueError("No choices supplied!")
            elif use_choices and use_kwchoices:
                raise ValueError("Both choices and probabilities supplied!")
            elif use_choices:
                if getattr(choices[0], "function_name", None) == "choice":
                    choices = [self.context.evaluate_raw(choice) for choice in choices]
                    rc = weighted_choice(choices)
                else:
                    rc = random.choice(choices)
                if hasattr(rc, "render"):
                    rc = self.context.evaluate_raw(rc)
            else:
                assert use_kwchoices and not use_choices
                choices = [
                    (parse_weight_str(self.context, value), key)
                    for key, value in kwchoices.items()
                ]
                rc = weighted_choice(choices)

            return rc

        @lazy
        def choice(
            self,
            pick,
            probability: FieldDefinition = None,
            when: FieldDefinition = None,
        ):
            """Supports the choice: sub-items used in `random_choice` or `if`"""
            if probability:
                probability = parse_weight_str(self.context, probability)
            return probability or when, pick

        def random_reference(self, tablename: str, scope: str = "current-iteration"):
            """Select a random, already-created row from 'sobject'

            - object: Owner
              count: 10
              fields:
                name: fake.name
            - object: Pet
              count: 10
              fields:
                ownedBy:
                    random_reference:
                        Owner

            See the docs for more info.
            """

            globls = self.context.interpreter.globals
            last_id = globls.transients.last_id_for_table(tablename)
            if last_id:
                if scope == "prior-and-current-iterations":
                    first_id = 1
                    warnings.warn("Global scope is an experimental feature.")
                elif scope == "current-iteration":
                    first_id = globls.first_new_id(tablename)
                    last_id = max(first_id, last_id)
                else:
                    raise DataGenError(
                        f"Scope must be 'prior-and-current-iterations' or 'current-iteration' not {scope}",
                        None,
                        None,
                    )
                return ObjectReference(tablename, random.randint(first_id, last_id))
            elif tablename in globls.transients.nicknamed_objects:
                raise DataGenError(
                    "Nicknames cannot be used in random_reference", None, None
                )
            else:
                raise DataGenError(f"There is no table named {tablename}", None, None)

        @lazy
        def if_(self, *choices: FieldDefinition):
            """Template helper for conditional choices.

            Supports structures like this:

            if:
                - choice:
                    when: ${{something}}
                    pick: A
                - choice:
                    when: ${{something}}
                    pick: B

            Pick-items can have arbitrary internal complexity.

            Pick-items are lazily evaluated.
            """
            if not choices:
                raise ValueError("No choices supplied!")

            choices = [self.context.evaluate_raw(choice) for choice in choices]
            for when, choice in choices[:-1]:
                if when is None:
                    raise SyntaxError(
                        "Every choice except the last one should have a when-clause"
                    )
            true_choices = (
                choice
                for when, choice in choices
                if when and render_boolean(self.context, when)
            )
            rc = next(true_choices, choices[-1][-1])  # default to last choice
            if hasattr(rc, "render"):
                rc = self.context.evaluate_raw(rc)
            return rc

        def _snowfakery_filename(self):
            template = self.context.field_vars()["template"]
            return template.filename

        @property
        def _unique_id_generator(self):
            if not self._uidgen:
                self._uidgen = UniqueId(self.context.interpreter).custom_functions()

            return self._uidgen

        def _unique_id(self):
            return self._unique_id_generator.default_uniqifier.unique_id

        def _unique_alpha_code(self):
            return self._unique_id_generator.default_alpha_code_generator.unique_id

        def debug(self, value):
            msg = f"DEBUG - {value} ({type(value)})\n"
            sys.stderr.write(msg)
            return value

    setattr(Functions, "if", Functions.if_)
    setattr(Functions, "relativedelta", relativedelta)
    setattr(Functions, "NULL", None)
    setattr(Functions, "null", None)
    setattr(Functions, "Null", None)
