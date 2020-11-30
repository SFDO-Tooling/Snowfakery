import random
from functools import lru_cache
from datetime import date, datetime
import dateutil.parser
from dateutil.relativedelta import relativedelta
from ast import literal_eval

from typing import Union, List, Tuple

from faker import Faker
from faker.providers.date_time import Provider as DateProvider

from .data_gen_exceptions import DataGenError

import snowfakery.data_generator_runtime  # noqa
from snowfakery.plugins import SnowfakeryPlugin, PluginContext, lazy

FieldDefinition = "snowfakery.data_generator_runtime_object_model.FieldDefinition"
ObjectRow = "snowfakery.data_generator_runtime.ObjectRow"

fake = Faker()

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
        ):
            """A YAML-embeddable function to construct a datetime from strings or integers"""
            return datetime(year, month, day, hour, minute, second, microsecond)

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
                return fake.date_between(start_date, end_date)
            except ValueError as e:
                if "empty range" not in str(e):
                    raise
            # swallow empty range errors per Python conventions

        def i18n_fake(self, locale: str, fake: str):
            faker = Faker(locale)
            func = getattr(faker, fake)
            return func()

        def random_number(self, min: int, max: int, step: int = 1) -> int:
            """Pick a random number between min and max like Python's randint."""
            return random.randrange(min, max + 1, step)

        def reference(self, x: Union[ObjectRow, str]):
            """YAML-embeddable function to Reference another object."""
            if hasattr(x, "id"):  # reference to an object with an id
                target = x
            elif isinstance(x, str):  # name of an object
                obj = self.context.field_vars().get(x)
                if not obj:
                    raise DataGenError(f"Cannot find an object named {x}", None, None)
                if not getattr(obj, "id", None):
                    raise DataGenError(
                        f"Reference to incorrect object type {obj}", None, None
                    )
                target = obj
            else:
                raise DataGenError(
                    f"Can't get reference to object of type {type(x)}: {x}", None, None
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

    setattr(Functions, "if", Functions.if_)
    setattr(Functions, "relativedelta", relativedelta)
