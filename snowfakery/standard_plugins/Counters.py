from itertools import count
from datetime import timedelta, date
import typing as T

from faker.providers.date_time import ParseError, Provider as DateProvider

from snowfakery import SnowfakeryPlugin
from snowfakery.plugins import PluginResultIterator, memorable
from snowfakery import data_gen_exceptions as exc
from snowfakery.utils.validation_utils import resolve_value


# TODO: merge this with template_funcs equivalent
def try_parse_date(d):
    from snowfakery.template_funcs import parse_date

    if not isinstance(d, str) or not DateProvider.regex.fullmatch(d):
        try:
            return parse_date(d)
        except Exception:  # let's hope its something faker can parse
            try:
                return DateProvider._parse_date(d)
            except ParseError as e:
                raise exc.DataGenValueError(d) from e


class NumberCounter(PluginResultIterator):
    def __init__(self, start=1, step=1):
        start = 1 if start is None else start
        self.counter = count(start, step)
        self.result = {
            "start": start,
            "step": step,
        }  # for serialization during continuation

    def next(self):
        return next(self.counter)


class DateCounter(PluginResultIterator):
    def __init__(self, start_date: T.Union[str, date] = "today", step: str = "+1d"):
        self.start_date = try_parse_date(start_date)
        if not self.start_date:  # pragma: no cover
            raise exc.DataGenError(f"Cannot parse start date {start_date}")
        step = DateProvider._parse_timedelta(step)
        self.counter = count(0, step)
        self.result = {
            "start": self.start_date,
            "step": step,
        }  # for serialization during continuation

    def next(self):
        offset = next(self.counter)
        return self.start_date + timedelta(seconds=offset)


class Counters(SnowfakeryPlugin):
    class Functions:
        @memorable
        def NumberCounter(
            self,
            _=None,
            *,
            start=1,
            step=1,
            name=None,
            parent=None,
        ):
            return NumberCounter(start, step)

        @memorable
        def DateCounter(
            self,
            _=None,
            *,
            start_date,
            step,
            name=None,
            parent=None,
        ):
            return DateCounter(start_date=start_date, step=step)

    class Validators:
        """Validators for Counters plugin functions."""

        @staticmethod
        def validate_NumberCounter(sv, context):
            """Validate Counters.NumberCounter(start=1, step=1, name=None, parent=None)."""
            kwargs = getattr(sv, "kwargs", {})

            # Validate start
            if "start" in kwargs:
                start_val = resolve_value(kwargs["start"], context)

                if start_val is not None:
                    # ERROR: Must be integer
                    if not isinstance(start_val, int):
                        context.add_error(
                            f"Counters.NumberCounter: 'start' must be an integer, got {type(start_val).__name__}",
                            getattr(sv, "filename", None),
                            getattr(sv, "line_num", None),
                        )

            # Validate step
            if "step" in kwargs:
                step_val = resolve_value(kwargs["step"], context)

                if step_val is not None:
                    # ERROR: Must be integer
                    if not isinstance(step_val, int):
                        context.add_error(
                            f"Counters.NumberCounter: 'step' must be an integer, got {type(step_val).__name__}",
                            getattr(sv, "filename", None),
                            getattr(sv, "line_num", None),
                        )
                    # ERROR: Cannot be zero
                    elif step_val == 0:
                        context.add_error(
                            "Counters.NumberCounter: 'step' cannot be zero",
                            getattr(sv, "filename", None),
                            getattr(sv, "line_num", None),
                        )

            # Validate name (optional warning)
            if "name" in kwargs:
                name_val = resolve_value(kwargs["name"], context)

                if name_val is not None and not isinstance(name_val, str):
                    context.add_warning(
                        f"Counters.NumberCounter: 'name' should be a string, got {type(name_val).__name__}",
                        getattr(sv, "filename", None),
                        getattr(sv, "line_num", None),
                    )

            # WARNING: Unknown parameters
            valid_params = {"start", "step", "name", "parent", "_"}
            unknown = set(kwargs.keys()) - valid_params
            if unknown:
                context.add_warning(
                    f"Counters.NumberCounter: Unknown parameter(s): {', '.join(sorted(unknown))}",
                    getattr(sv, "filename", None),
                    getattr(sv, "line_num", None),
                )

            # Return mock: counter object that returns start value
            start = 1
            if "start" in kwargs:
                start_val = resolve_value(kwargs["start"], context)
                if isinstance(start_val, int):
                    start = start_val

            # Return a mock counter object with a next() method
            return type("MockNumberCounter", (), {"next": lambda self: start})()

        @staticmethod
        def validate_DateCounter(sv, context):
            """Validate Counters.DateCounter(start_date, step, name=None, parent=None)."""
            kwargs = getattr(sv, "kwargs", {})

            # ERROR: Required parameters
            if "start_date" not in kwargs:
                context.add_error(
                    "Counters.DateCounter: Missing required parameter 'start_date'",
                    getattr(sv, "filename", None),
                    getattr(sv, "line_num", None),
                )

            if "step" not in kwargs:
                context.add_error(
                    "Counters.DateCounter: Missing required parameter 'step'",
                    getattr(sv, "filename", None),
                    getattr(sv, "line_num", None),
                )

            # If both required params are missing, return early
            if "start_date" not in kwargs or "step" not in kwargs:
                return

            # Validate start_date using the existing try_parse_date function
            start_date_val = resolve_value(kwargs["start_date"], context)

            if start_date_val is not None:
                try:
                    # Try to parse the date to validate it
                    try_parse_date(start_date_val)
                except (
                    exc.DataGenValueError,
                    exc.DataGenError,
                    ValueError,
                    TypeError,
                ) as e:
                    context.add_error(
                        f"Counters.DateCounter: Invalid 'start_date' value: {str(e)}",
                        getattr(sv, "filename", None),
                        getattr(sv, "line_num", None),
                    )

            # Validate step using DateProvider._parse_timedelta
            step_val = resolve_value(kwargs["step"], context)

            if step_val is not None:
                # ERROR: Must be string
                if not isinstance(step_val, str):
                    context.add_error(
                        f"Counters.DateCounter: 'step' must be a string, got {type(step_val).__name__}",
                        getattr(sv, "filename", None),
                        getattr(sv, "line_num", None),
                    )
                else:
                    # Validate step format using DateProvider's parser
                    try:
                        DateProvider._parse_timedelta(step_val)
                    except (ValueError, AttributeError, TypeError):
                        context.add_error(
                            f"Counters.DateCounter: Invalid 'step' format '{step_val}'. "
                            f"Expected format: +/-<number><unit> (e.g., +1d, -1w, +1M, +1y)",
                            getattr(sv, "filename", None),
                            getattr(sv, "line_num", None),
                        )

            # Validate name (optional warning)
            if "name" in kwargs:
                name_val = resolve_value(kwargs["name"], context)

                if name_val is not None and not isinstance(name_val, str):
                    context.add_warning(
                        f"Counters.DateCounter: 'name' should be a string, got {type(name_val).__name__}",
                        getattr(sv, "filename", None),
                        getattr(sv, "line_num", None),
                    )

            # WARNING: Unknown parameters
            valid_params = {"start_date", "step", "name", "parent", "_"}
            unknown = set(kwargs.keys()) - valid_params
            if unknown:
                context.add_warning(
                    f"Counters.DateCounter: Unknown parameter(s): {', '.join(sorted(unknown))}",
                    getattr(sv, "filename", None),
                    getattr(sv, "line_num", None),
                )

            # Return mock: counter object that returns start_date
            start_date = date.today()
            if "start_date" in kwargs:
                start_date_val = resolve_value(kwargs["start_date"], context)
                if start_date_val is not None:
                    try:
                        # Try to parse the date
                        parsed_date = try_parse_date(start_date_val)
                        if parsed_date:
                            start_date = parsed_date
                    except Exception:
                        pass

            # Return a mock counter object with a next() method
            return type("MockDateCounter", (), {"next": lambda self: start_date})()
