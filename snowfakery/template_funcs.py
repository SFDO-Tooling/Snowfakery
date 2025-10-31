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
from snowfakery.utils.validation_utils import resolve_value, get_fuzzy_match
from datetime import date as date_constructor, datetime as datetime_constructor

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

    class Validators:
        """Static validators for standard functions."""

        @staticmethod
        def check_required_params(sv, context, required_params, func_name):
            """Helper to check required parameters and return False if any missing.

            Args:
                sv: StructuredValue with kwargs to check
                context: ValidationContext to add errors to
                required_params: List or set of required parameter names
                func_name: Name of function for error messages

            Returns:
                True if all required params present, False if any missing
            """
            kwargs = sv.kwargs if hasattr(sv, "kwargs") else {}
            missing = [p for p in required_params if p not in kwargs]
            if missing:
                context.add_error(
                    f"{func_name}: Missing required parameter(s): {', '.join(missing)}",
                    getattr(sv, "filename", None),
                    getattr(sv, "line_num", None),
                )
                return False
            return True

        @staticmethod
        def validate_random_number(sv, context):
            """Validate random_number(min, max, step)"""

            # ERROR: Required parameters
            if not StandardFuncs.Validators.check_required_params(
                sv, context, ["min", "max"], "random_number"
            ):
                return

            kwargs = sv.kwargs if hasattr(sv, "kwargs") else {}

            # Resolve values
            min_val = resolve_value(kwargs.get("min"), context)
            max_val = resolve_value(kwargs.get("max"), context)
            step_val = resolve_value(kwargs.get("step", 1), context)

            # ERROR: Type checking
            if min_val is not None and not isinstance(min_val, (int, float)):
                context.add_error(
                    "random_number: 'min' must be an integer",
                    getattr(sv, "filename", None),
                    getattr(sv, "line_num", None),
                )
            if max_val is not None and not isinstance(max_val, (int, float)):
                context.add_error(
                    "random_number: 'max' must be an integer",
                    getattr(sv, "filename", None),
                    getattr(sv, "line_num", None),
                )

            # ERROR: Logical constraints
            if isinstance(min_val, (int, float)) and isinstance(max_val, (int, float)):
                if min_val > max_val:
                    context.add_error(
                        f"random_number: 'min' ({min_val}) must be <= 'max' ({max_val})",
                        getattr(sv, "filename", None),
                        getattr(sv, "line_num", None),
                    )

            # ERROR: Step validation
            if step_val is not None:
                if not isinstance(step_val, int) or step_val <= 0:
                    context.add_error(
                        "random_number: 'step' must be a positive integer",
                        getattr(sv, "filename", None),
                        getattr(sv, "line_num", None),
                    )

            # WARNING: Unknown parameters
            valid_params = {"min", "max", "step"}
            unknown = set(kwargs.keys()) - valid_params
            if unknown:
                context.add_warning(
                    f"random_number: Unknown parameter(s): {', '.join(unknown)}",
                    getattr(sv, "filename", None),
                    getattr(sv, "line_num", None),
                )

        @staticmethod
        def validate_reference(sv, context):
            """Validate reference(x, object, id)"""

            kwargs = sv.kwargs if hasattr(sv, "kwargs") else {}
            args = getattr(sv, "args", [])

            # Determine if using x or object+id form
            has_x = len(args) > 0 or "x" in kwargs
            has_object = "object" in kwargs
            has_id = "id" in kwargs

            # ERROR: Must specify either x OR (object AND id)
            if not has_x and not (has_object and has_id):
                context.add_error(
                    "reference: Must specify either positional argument or both 'object' and 'id'",
                    getattr(sv, "filename", None),
                    getattr(sv, "line_num", None),
                )
                return

            # ERROR: Cannot mix x and object/id
            if has_x and (has_object or has_id):
                context.add_error(
                    "reference: Cannot specify both positional argument and 'object'/'id'",
                    getattr(sv, "filename", None),
                    getattr(sv, "line_num", None),
                )
                return

            # Validate object exists
            if has_x:
                ref_name = resolve_value(args[0] if args else kwargs["x"], context)
                if ref_name and isinstance(ref_name, str):
                    # Allow forward references for reference function
                    obj = context.resolve_object(ref_name, allow_forward_ref=True)
                    if not obj:
                        suggestion = get_fuzzy_match(
                            ref_name,
                            list(context.all_objects.keys())
                            + list(context.all_nicknames.keys()),
                        )
                        msg = f"reference: Unknown object/nickname '{ref_name}'"
                        if suggestion:
                            msg += f". Did you mean '{suggestion}'?"
                        context.add_error(
                            msg,
                            getattr(sv, "filename", None),
                            getattr(sv, "line_num", None),
                        )

            elif has_object:
                obj_name = resolve_value(kwargs["object"], context)
                if obj_name and isinstance(obj_name, str):
                    # Allow forward references for reference function
                    if obj_name not in context.all_objects:
                        suggestion = get_fuzzy_match(
                            obj_name, list(context.all_objects.keys())
                        )
                        msg = f"reference: Unknown object type '{obj_name}'"
                        if suggestion:
                            msg += f". Did you mean '{suggestion}'?"
                        context.add_error(
                            msg,
                            getattr(sv, "filename", None),
                            getattr(sv, "line_num", None),
                        )

                # Validate id is numeric
                id_val = resolve_value(kwargs["id"], context)
                if id_val is not None and not isinstance(id_val, (int, float)):
                    context.add_warning(
                        "reference: 'id' must be numeric",
                        getattr(sv, "filename", None),
                        getattr(sv, "line_num", None),
                    )

        @staticmethod
        def validate_random_choice(sv, context):
            """Validate random_choice(*choices, **kwchoices)"""

            kwargs = sv.kwargs if hasattr(sv, "kwargs") else {}
            args = getattr(sv, "args", [])

            # ERROR: Must have at least one choice
            if not args and not kwargs:
                context.add_error(
                    "random_choice: No choices provided",
                    getattr(sv, "filename", None),
                    getattr(sv, "line_num", None),
                )
                return

            # ERROR: Cannot mix list and dict formats
            if args and kwargs:
                context.add_error(
                    "random_choice: Cannot mix list-based and probability-based choices",
                    getattr(sv, "filename", None),
                    getattr(sv, "line_num", None),
                )
                return

            # Validate probability format if using dict
            if kwargs:
                total = 0
                has_percentages = False

                for key, prob in kwargs.items():
                    prob_val = resolve_value(prob, context)

                    if prob_val is not None:
                        # Check if it's a string percentage
                        if isinstance(prob_val, str) and prob_val.endswith("%"):
                            has_percentages = True
                            try:
                                numeric_val = float(prob_val.rstrip("%"))

                                # ERROR: Must be positive
                                if numeric_val < 0:
                                    context.add_error(
                                        "random_choice: Probability must be positive",
                                        getattr(sv, "filename", None),
                                        getattr(sv, "line_num", None),
                                    )

                                # ERROR: Individual > 100%
                                if numeric_val > 100:
                                    context.add_error(
                                        f"random_choice: Probability {prob_val} exceeds 100%",
                                        getattr(sv, "filename", None),
                                        getattr(sv, "line_num", None),
                                    )

                                total += numeric_val
                            except ValueError:
                                context.add_error(
                                    "random_choice: Probability must be numeric or percentage (e.g., '50%')",
                                    getattr(sv, "filename", None),
                                    getattr(sv, "line_num", None),
                                )
                        elif isinstance(prob_val, (int, float)):
                            # ERROR: Must be positive
                            if prob_val < 0:
                                context.add_error(
                                    "random_choice: Probability must be positive",
                                    getattr(sv, "filename", None),
                                    getattr(sv, "line_num", None),
                                )
                        else:
                            context.add_error(
                                "random_choice: Probability must be numeric or percentage (e.g., '50%')",
                                getattr(sv, "filename", None),
                                getattr(sv, "line_num", None),
                            )

                # ERROR: Probabilities sum to 0
                if has_percentages and total == 0:
                    context.add_error(
                        "random_choice: Probabilities sum to zero",
                        getattr(sv, "filename", None),
                        getattr(sv, "line_num", None),
                    )

                # WARNING: Probabilities don't add to 100%
                if has_percentages and total != 0 and total != 100:
                    context.add_warning(
                        f"random_choice: Warning - probabilities add up to {total}%, expected 100%",
                        getattr(sv, "filename", None),
                        getattr(sv, "line_num", None),
                    )

        @staticmethod
        def validate_date(sv, context):
            """Validate date(datespec=None, *, year=None, month=None, day=None)"""

            kwargs = sv.kwargs if hasattr(sv, "kwargs") else {}
            args = getattr(sv, "args", [])

            # Get datespec (positional or keyword)
            datespec = args[0] if args else kwargs.get("datespec")
            year = kwargs.get("year")
            month = kwargs.get("month")
            day = kwargs.get("day")

            # ERROR: Cannot specify both datespec and components
            if datespec and any([year, month, day]):
                context.add_error(
                    "date: Cannot specify 'datespec' with 'year', 'month', or 'day'",
                    getattr(sv, "filename", None),
                    getattr(sv, "line_num", None),
                )
                return

            # If using components, validate them
            if any([year, month, day]):
                # ERROR: All three required together
                if not all([year, month, day]):
                    context.add_error(
                        "date: Must specify 'year', 'month', and 'day' together",
                        getattr(sv, "filename", None),
                        getattr(sv, "line_num", None),
                    )
                    return

                # Resolve and validate
                year_val = resolve_value(year, context)
                month_val = resolve_value(month, context)
                day_val = resolve_value(day, context)

                if all([isinstance(v, int) for v in [year_val, month_val, day_val]]):
                    try:
                        date_constructor(year_val, month_val, day_val)
                    except (ValueError, TypeError) as e:
                        context.add_error(
                            f"date: Invalid date - {str(e)}",
                            getattr(sv, "filename", None),
                            getattr(sv, "line_num", None),
                        )

            # If using datespec, validate it
            elif datespec:
                datespec_val = resolve_value(datespec, context)
                if isinstance(datespec_val, str):
                    # Skip validation for Jinja expressions
                    if not ("{{" in datespec_val or "{%" in datespec_val):
                        try:
                            parse_date(datespec_val)
                        except Exception:
                            context.add_error(
                                f"date: Invalid date string '{datespec_val}'",
                                getattr(sv, "filename", None),
                                getattr(sv, "line_num", None),
                            )

            # WARNING: Unknown parameters
            valid_params = {"datespec", "year", "month", "day"}
            unknown = set(kwargs.keys()) - valid_params
            if unknown:
                context.add_warning(
                    f"date: Unknown parameter(s): {', '.join(unknown)}",
                    getattr(sv, "filename", None),
                    getattr(sv, "line_num", None),
                )

        @staticmethod
        def validate_datetime(sv, context):
            """Validate datetime(datetimespec=None, *, year, month, day, hour, minute, second, microsecond, timezone)"""

            kwargs = sv.kwargs if hasattr(sv, "kwargs") else {}
            args = getattr(sv, "args", [])

            datetimespec = args[0] if args else kwargs.get("datetimespec")
            components = [
                "year",
                "month",
                "day",
                "hour",
                "minute",
                "second",
                "microsecond",
            ]
            has_components = any([kwargs.get(c) for c in components])

            # ERROR: Cannot specify both datetimespec and components
            if datetimespec and has_components:
                context.add_error(
                    "datetime: Cannot specify 'datetimespec' with other parameters",
                    getattr(sv, "filename", None),
                    getattr(sv, "line_num", None),
                )
                return

            # Validate components if provided
            if has_components:
                year = resolve_value(kwargs.get("year"), context)
                month = resolve_value(kwargs.get("month"), context)
                day = resolve_value(kwargs.get("day"), context)
                hour = resolve_value(kwargs.get("hour", 0), context)
                minute = resolve_value(kwargs.get("minute", 0), context)
                second = resolve_value(kwargs.get("second", 0), context)
                microsecond = resolve_value(kwargs.get("microsecond", 0), context)

                # Try to construct datetime if all are literals
                if all(
                    [
                        isinstance(v, int)
                        for v in [year, month, day, hour, minute, second, microsecond]
                    ]
                ):
                    try:
                        datetime_constructor(
                            year, month, day, hour, minute, second, microsecond
                        )
                    except (ValueError, TypeError) as e:
                        context.add_error(
                            f"datetime: Invalid datetime - {str(e)}",
                            getattr(sv, "filename", None),
                            getattr(sv, "line_num", None),
                        )

            # Validate datetimespec if provided
            elif datetimespec:
                spec_val = resolve_value(datetimespec, context)
                if isinstance(spec_val, str):
                    # Skip validation for Jinja expressions
                    if not ("{{" in spec_val or "{%" in spec_val):
                        try:
                            parse_datetimespec(spec_val)
                        except Exception:
                            context.add_error(
                                f"datetime: Invalid datetime string '{spec_val}'",
                                getattr(sv, "filename", None),
                                getattr(sv, "line_num", None),
                            )

            # WARNING: Unknown parameters
            valid_params = {
                "datetimespec",
                "year",
                "month",
                "day",
                "hour",
                "minute",
                "second",
                "microsecond",
                "timezone",
            }
            unknown = set(kwargs.keys()) - valid_params
            if unknown:
                context.add_warning(
                    f"datetime: Unknown parameter(s): {', '.join(unknown)}",
                    getattr(sv, "filename", None),
                    getattr(sv, "line_num", None),
                )

        @staticmethod
        def validate_date_between(sv, context):
            """Validate date_between(*, start_date, end_date, timezone)"""

            # ERROR: Required parameters
            if not StandardFuncs.Validators.check_required_params(
                sv, context, ["start_date", "end_date"], "date_between"
            ):
                return

            kwargs = sv.kwargs if hasattr(sv, "kwargs") else {}

            # Validate date strings
            for param in ["start_date", "end_date"]:
                date_val = resolve_value(kwargs[param], context)
                if isinstance(date_val, str):
                    # Try Faker relative format or parse_date
                    # If both fail, we still allow it - Faker might handle it (e.g., "today")
                    # This matches runtime behavior which passes unknown strings to Faker
                    if not DateProvider.regex.fullmatch(date_val):
                        try:
                            parse_date(date_val)
                        except Exception:
                            # Can't parse, but Faker might handle it (like "today")
                            # Only warn if it looks completely wrong
                            if not date_val.lower() in ["today", "now"]:
                                context.add_warning(
                                    f"date_between: Unknown date format '{date_val}' in '{param}' - will rely on Faker to parse",
                                    getattr(sv, "filename", None),
                                    getattr(sv, "line_num", None),
                                )

            # WARNING: Unknown parameters
            valid_params = {"start_date", "end_date", "timezone"}
            unknown = set(kwargs.keys()) - valid_params
            if unknown:
                context.add_warning(
                    f"date_between: Unknown parameter(s): {', '.join(unknown)}",
                    getattr(sv, "filename", None),
                    getattr(sv, "line_num", None),
                )

        @staticmethod
        def validate_datetime_between(sv, context):
            """Validate datetime_between(*, start_date, end_date, timezone)"""

            # ERROR: Required parameters
            if not StandardFuncs.Validators.check_required_params(
                sv, context, ["start_date", "end_date"], "datetime_between"
            ):
                return

            kwargs = sv.kwargs if hasattr(sv, "kwargs") else {}

            # Validate datetime strings
            for param in ["start_date", "end_date"]:
                dt_val = resolve_value(kwargs[param], context)
                if isinstance(dt_val, str):
                    if not DateProvider.regex.fullmatch(dt_val):
                        try:
                            parse_datetimespec(dt_val)
                        except Exception:
                            context.add_error(
                                f"datetime_between: Invalid datetime string '{dt_val}' in '{param}'",
                                getattr(sv, "filename", None),
                                getattr(sv, "line_num", None),
                            )

            # WARNING: Unknown parameters
            valid_params = {"start_date", "end_date", "timezone"}
            unknown = set(kwargs.keys()) - valid_params
            if unknown:
                context.add_warning(
                    f"datetime_between: Unknown parameter(s): {', '.join(unknown)}",
                    getattr(sv, "filename", None),
                    getattr(sv, "line_num", None),
                )

        @staticmethod
        def validate_relativedelta(sv, context):
            """Validate relativedelta(...) - basic parameter check"""

            kwargs = sv.kwargs if hasattr(sv, "kwargs") else {}

            known_params = {
                "years",
                "months",
                "days",
                "hours",
                "minutes",
                "seconds",
                "microseconds",
                "year",
                "month",
                "day",
                "hour",
                "minute",
                "second",
                "microsecond",
                "weekday",
            }

            # Validate numeric parameters
            for param, value in kwargs.items():
                if param in known_params:
                    val = resolve_value(value, context)
                    if val is not None and not isinstance(val, (int, float)):
                        context.add_warning(
                            f"relativedelta: Parameter '{param}' must be numeric",
                            getattr(sv, "filename", None),
                            getattr(sv, "line_num", None),
                        )

            # WARNING: Unknown parameters
            unknown = set(kwargs.keys()) - known_params
            if unknown:
                context.add_warning(
                    f"relativedelta: Unknown parameter(s): {', '.join(unknown)}",
                    getattr(sv, "filename", None),
                    getattr(sv, "line_num", None),
                )

        @staticmethod
        def validate_random_reference(sv, context):
            """Validate random_reference(to, *, parent, scope, unique)"""

            kwargs = sv.kwargs if hasattr(sv, "kwargs") else {}
            args = getattr(sv, "args", [])

            # Get 'to' parameter
            to = args[0] if args else kwargs.get("to")

            # ERROR: 'to' is required
            if not to:
                context.add_error(
                    "random_reference: Missing required parameter 'to'",
                    getattr(sv, "filename", None),
                    getattr(sv, "line_num", None),
                )
                return

            # Validate 'to' object exists (allow forward references)
            to_val = resolve_value(to, context)
            if to_val and isinstance(to_val, str):
                if to_val not in context.all_objects:
                    suggestion = get_fuzzy_match(
                        to_val, list(context.all_objects.keys())
                    )
                    msg = f"random_reference: Unknown object type '{to_val}'"
                    if suggestion:
                        msg += f". Did you mean '{suggestion}'?"
                    context.add_error(
                        msg,
                        getattr(sv, "filename", None),
                        getattr(sv, "line_num", None),
                    )

            # Validate 'scope'
            scope = kwargs.get("scope", "current-iteration")
            scope_val = resolve_value(scope, context)
            if scope_val and isinstance(scope_val, str):
                valid_scopes = ["current-iteration", "prior-and-current-iterations"]
                if scope_val not in valid_scopes:
                    context.add_error(
                        f"random_reference: 'scope' must be one of: {', '.join(valid_scopes)}",
                        getattr(sv, "filename", None),
                        getattr(sv, "line_num", None),
                    )

            # Validate 'unique'
            unique = kwargs.get("unique", False)
            unique_val = resolve_value(unique, context)
            if unique_val is not None and not isinstance(unique_val, bool):
                context.add_error(
                    "random_reference: 'unique' must be boolean (true/false)",
                    getattr(sv, "filename", None),
                    getattr(sv, "line_num", None),
                )

            # Validate 'parent' object exists (allow forward references)
            parent = kwargs.get("parent")
            if parent:
                parent_val = resolve_value(parent, context)
                if parent_val and isinstance(parent_val, str):
                    if parent_val not in context.all_objects:
                        suggestion = get_fuzzy_match(
                            parent_val, list(context.all_objects.keys())
                        )
                        msg = f"random_reference: Unknown parent object type '{parent_val}'"
                        if suggestion:
                            msg += f". Did you mean '{suggestion}'?"
                        context.add_error(
                            msg,
                            getattr(sv, "filename", None),
                            getattr(sv, "line_num", None),
                        )

                # WARNING: parent without unique
                if not unique_val:
                    context.add_warning(
                        "random_reference: 'parent' parameter is only meaningful with 'unique: true'",
                        getattr(sv, "filename", None),
                        getattr(sv, "line_num", None),
                    )

            # WARNING: Unknown parameters
            valid_params = {"to", "parent", "scope", "unique"}
            unknown = set(kwargs.keys()) - valid_params
            if unknown:
                context.add_warning(
                    f"random_reference: Unknown parameter(s): {', '.join(unknown)}",
                    getattr(sv, "filename", None),
                    getattr(sv, "line_num", None),
                )

        @staticmethod
        def validate_choice(sv, context):
            """Validate choice(pick, probability=None, when=None)"""
            kwargs = sv.kwargs if hasattr(sv, "kwargs") else {}
            args = getattr(sv, "args", [])

            # Get pick
            pick = args[0] if args else kwargs.get("pick")

            # ERROR: 'pick' is required
            if not pick:
                context.add_error(
                    "choice: Missing required parameter 'pick'",
                    getattr(sv, "filename", None),
                    getattr(sv, "line_num", None),
                )
                return

            # WARNING: Cannot use both probability and when
            if "probability" in kwargs and "when" in kwargs:
                context.add_warning(
                    "choice: Cannot specify both 'probability' and 'when'",
                    getattr(sv, "filename", None),
                    getattr(sv, "line_num", None),
                )

            # WARNING: Unknown parameters
            valid_params = {"pick", "probability", "when"}
            unknown = set(kwargs.keys()) - valid_params
            if unknown:
                context.add_warning(
                    f"choice: Unknown parameter(s): {', '.join(unknown)}",
                    getattr(sv, "filename", None),
                    getattr(sv, "line_num", None),
                )

        @staticmethod
        def validate_if_(sv, context):
            """Validate if(*choices)"""
            kwargs = sv.kwargs if hasattr(sv, "kwargs") else {}
            args = getattr(sv, "args", [])

            # ERROR: Must have at least one choice
            if not args and not kwargs:
                context.add_error(
                    "if: No choices provided",
                    getattr(sv, "filename", None),
                    getattr(sv, "line_num", None),
                )
                return

            # Check that all but last have 'when' clause
            # This is simplified - full validation would require checking nested structures
            if len(args) > 1:
                context.add_warning(
                    "if: Ensure all choices except the last have 'when' clause",
                    getattr(sv, "filename", None),
                    getattr(sv, "line_num", None),
                )

        @staticmethod
        def validate_snowfakery_filename(sv, context):
            """Validate snowfakery_filename() - takes no parameters"""
            kwargs = sv.kwargs if hasattr(sv, "kwargs") else {}
            args = getattr(sv, "args", [])

            # ERROR: No parameters allowed
            if args or kwargs:
                context.add_error(
                    "snowfakery_filename: Takes no parameters",
                    getattr(sv, "filename", None),
                    getattr(sv, "line_num", None),
                )

        @staticmethod
        def validate_unique_id(sv, context):
            """Validate unique_id() - takes no parameters"""
            kwargs = sv.kwargs if hasattr(sv, "kwargs") else {}
            args = getattr(sv, "args", [])

            # ERROR: No parameters allowed
            if args or kwargs:
                context.add_error(
                    "unique_id: Takes no parameters",
                    getattr(sv, "filename", None),
                    getattr(sv, "line_num", None),
                )

        @staticmethod
        def validate_unique_alpha_code(sv, context):
            """Validate unique_alpha_code() - takes no parameters"""
            kwargs = sv.kwargs if hasattr(sv, "kwargs") else {}
            args = getattr(sv, "args", [])

            # ERROR: No parameters allowed
            if args or kwargs:
                context.add_error(
                    "unique_alpha_code: Takes no parameters",
                    getattr(sv, "filename", None),
                    getattr(sv, "line_num", None),
                )

        @staticmethod
        def validate_debug(sv, context):
            """Validate debug(value) - requires exactly one argument"""
            kwargs = sv.kwargs if hasattr(sv, "kwargs") else {}
            args = getattr(sv, "args", [])

            # ERROR: Requires exactly one argument
            if len(args) != 1 and "value" not in kwargs:
                context.add_error(
                    "debug: Requires exactly one argument",
                    getattr(sv, "filename", None),
                    getattr(sv, "line_num", None),
                )
