from itertools import count
from datetime import timedelta, date
import typing as T

from faker.providers.date_time import ParseError, Provider as DateProvider

from snowfakery import SnowfakeryPlugin
from snowfakery.plugins import PluginResultIterator, memorable
from snowfakery import data_gen_exceptions as exc


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
