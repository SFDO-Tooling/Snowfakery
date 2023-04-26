import random
import sys
from ast import literal_eval
from datetime import date, datetime
from functools import lru_cache
from datetime import timezone
from typing import Any, List, Tuple, Union

import dateutil.parser
from dateutil.relativedelta import relativedelta
from faker import Faker
from faker.providers.date_time import Provider as DateProvider

import snowfakery.data_generator_runtime  # noqa
from snowfakery.fakedata.fake_data_generator import UTCAsRelDelta, _normalize_timezone
from snowfakery.object_rows import ObjectReference
from snowfakery.plugins import PluginContext, SnowfakeryPlugin, lazy, memorable
from snowfakery.row_history import RandomReferenceContext
from snowfakery.standard_plugins.UniqueId import UniqueId
from snowfakery.utils.template_utils import StringGenerator

from .data_gen_exceptions import DataGenError

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


@lru_cache(maxsize=512)
def parse_datetimespec(d: Union[str, datetime, date]) -> datetime:
    """Parse a string, datetime or date into a datetime."""
    if isinstance(d, datetime):
        if not d.tzinfo:
            d = d.replace(tzinfo=timezone.utc)
        return d
    elif isinstance(d, str):
        if d == "now":
            return datetime.now(tz=timezone.utc)
        elif d == "today":
            return datetime.combine(
                date.today(), datetime.min.time(), tzinfo=timezone.utc
            )
        d = dateutil.parser.parse(d)
        if not d.tzinfo:
            d = d.replace(tzinfo=timezone.utc)
        return d
    elif isinstance(d, date):
        return datetime.combine(d, datetime.min.time(), tzinfo=timezone.utc)


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
                if any((day, month, year)):
                    raise DataGenError(
                        "Should not specify a date specification and also day or month or year."
                    )
                return parse_date(datespec)
            else:
                return date(year, month, day)

        def datetime(
            self,
            datetimespec=None,
            *,
            year: Union[str, int] = None,
            month: Union[str, int] = None,
            day: Union[str, int] = None,
            hour=0,
            minute=0,
            second=0,
            microsecond=0,
            timezone=UTCAsRelDelta,
        ):
            """A YAML-embeddable function to construct a datetime from strings or integers"""
            timezone = _normalize_timezone(timezone)
            if datetimespec:
                if any((day, month, year, hour, minute, second, microsecond)):
                    raise DataGenError(
                        "Should not specify a date specification and also other parameters."
                    )
                dt = parse_datetimespec(datetimespec)
                dt = dt.replace(tzinfo=timezone)
            elif not (any((year, month, day, hour, minute, second, microsecond))):
                # no dt specification provided at all...just use now()
                dt = datetime.now(timezone)
            else:
                dt = datetime(
                    year, month, day, hour, minute, second, microsecond, timezone
                )

            return dt

        def date_between(self, *, start_date, end_date, timezone=UTCAsRelDelta):
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

        def datetime_between(self, *, start_date, end_date, timezone=UTCAsRelDelta):
            """A YAML-embeddable function to pick a datetime between two ranges"""

            start_date = self.datetime(start_date)
            end_date = self.datetime(end_date)

            timezone = _normalize_timezone(timezone)
            if end_date < start_date:
                raise DataGenError("End date is before start date")

            return self._faker_for_dates.date_time_between(
                start_date, end_date, tzinfo=timezone
            )

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
                except (ValueError, TypeError):
                    raise DataGenError("Cannot interpret `id` as an integer")
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

        @memorable
        def random_reference(
            self,
            to: str,
            *,
            parent: str = None,
            scope: str = "current-iteration",
            unique: bool = False,
        ) -> "RandomReferenceContext":
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
            return RandomReferenceContext(
                self.context.interpreter.row_history, to, scope, unique
            )

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
