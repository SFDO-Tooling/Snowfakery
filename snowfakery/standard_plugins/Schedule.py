import collections
import re
import typing as T
import snowfakery.data_gen_exceptions as exc
from dateutil.rrule import rrule, rruleset
from dateutil import rrule as rrule_mod
from datetime import datetime, date, time, timezone
from snowfakery import PluginResultIterator
from snowfakery.plugins import SnowfakeryPlugin, memorable
from snowfakery.template_funcs import parse_datetimespec, parse_date


# Note

#   As soon as the base rule and the exclusion differ by even a second,
#   the exclusion doesn't exclude properly. (I think microseconds are okay.)
#
#   E.g. if I exclude very Monday in December, but the "Monday" is Monday at 3:30
#        and the days are scheduled for 3:31, then the exclusion won't apply.


FREQ_STRS = {
    frequency: getattr(rrule_mod, frequency)
    for frequency in [
        "YEARLY",
        "MONTHLY",
        "WEEKLY",
        "DAILY",
        "HOURLY",
        "MINUTELY",
        "SECONDLY",
    ]
}


WEEKDAYS = {
    day: getattr(rrule_mod, day) for day in ["MO", "TU", "WE", "TH", "FR", "SA", "SU"]
}


def is_datetime(dt: str):
    return bool(set(dt).intersection(" TZ"))


class CalendarRule(PluginResultIterator):
    def __init__(
        self,
        freq: str,
        start_date=None,
        interval=1,
        count=None,
        until=None,
        bysetpos=None,  # undocumented feature, for now
        bymonth=None,
        bymonthday=None,
        byyearday=None,
        byeaster=None,  # undocumented feature for now
        byweekno=None,  # undocumented feature for now
        byweekday=None,
        byhour=None,
        byminute=None,
        bysecond=None,
        cache=False,  # undocumented feature for now
        exclude=None,
        include=None,
        use_undocumented_features=False,
    ):
        if (not use_undocumented_features) and any(
            [bysetpos, byeaster, cache, byweekno]
        ):
            raise exc.DataGenValueError(
                "That feature is undocumented and unsupported. "
                "Use the `use_undocumented_features: True` argument to use it regardless."
            )
        self._set_start_date(start_date)
        wkst = rrule_mod.SU  # Standardize on Sunday as start of week globally
        # Could make this parameterizable if there is demand for it.
        bysetpos = process_list_of_ints(bysetpos)
        bymonth = process_list_of_ints(bymonth)
        bymonthday = process_list_of_ints(bymonthday)
        byyearday = process_list_of_ints(byyearday)
        byeaster = process_list_of_ints(byeaster)
        byhour = process_list_of_ints(byhour)
        byminute = process_list_of_ints(byminute)
        bysecond = process_list_of_ints(bysecond)

        until = self._set_until(until)

        freq = self._normalize_frequency(freq)

        if byweekday:
            byweekday = self._normalize_weekday(byweekday)

        self.ruleset = rruleset(cache)
        self.rrule = rrule(
            freq=freq,
            dtstart=self.start_date,
            interval=interval,
            wkst=wkst,
            count=count,
            until=until,
            bysetpos=bysetpos,  # undocumented feature for now
            bymonth=bymonth,  # undocumented feature for now
            bymonthday=bymonthday,
            byyearday=byyearday,
            byeaster=byeaster,  # undocumented feature for now
            byweekno=byweekno,
            byweekday=byweekday,
            byhour=byhour,
            byminute=byminute,
            bysecond=bysecond,
            cache=cache,
        )
        self.ruleset.rrule(self.rrule)

        self.compound = include or exclude
        if exclude:
            self._process_special_cases(exclude, "exclude")

        if include:
            self._process_special_cases(include, "include")

        self.iterator = iter(self)

    def _set_start_date(self, start_date):

        if isinstance(start_date, str):
            self.start_date = parse_datetimespec(start_date)
            assert self.start_date.tzinfo
            precision = datetime if is_datetime(start_date) else date
        elif isinstance(start_date, datetime):
            self.start_date = start_date
            precision = datetime
        elif isinstance(start_date, date):
            self.start_date = datetime.combine(
                start_date, time(hour=0, minute=0, second=0, tzinfo=timezone.utc)
            )
            precision = date
        elif not start_date:
            self.start_date = datetime.now()
            precision = datetime
        else:
            raise TypeError(
                f"`start_date` ({start_date}) is of unknown type {type(start_date)}"
            )
        if not self.start_date.tzinfo:
            self.start_date = self.start_date.replace(tzinfo=timezone.utc)
        assert precision in (date, datetime)

        self._set_generate_output(precision)

    def _set_until(self, until: T.Union[str, date, datetime, None]):
        if isinstance(until, str):
            if is_datetime(until):
                until = parse_datetimespec(until)
            else:
                until = datetime.combine(parse_date(until), self.start_date.time())

        elif isinstance(until, date):
            until = datetime.combine(until, self.start_date.time(), tzinfo=timezone.utc)
        elif until:
            raise exc.DataGenTypeError(
                f"`until` parameter ({until}) is of unexpected type {until}"
            )

        if until:
            until = until.replace(tzinfo=timezone.utc)
        return until

    def _set_generate_output(self, precision):
        assert precision in (date, datetime)
        if precision is date:
            self.next = self._next_date
        elif precision is datetime:
            self.next = self._next_datetime
        else:  # pragma: no cover
            assert False, "Should be unreachable"

    def _process_special_cases(self, case, action):
        if action == "exclude":
            add_rule = self.ruleset.exrule
            add_date = self.ruleset.exdate
        elif action == "include":
            add_rule = self.ruleset.rrule
            add_date = self.ruleset.rdate
        else:  # pragma: no cover   -   Should be unreachable
            assert action in ("include", "exclude"), "Bad action!"

        if isinstance(case, (list, tuple)):
            for case in case:
                self._process_special_cases(case, action)
        elif isinstance(case, CalendarRule):
            # assert (
            #     not case.compound
            # ), "Cannot recursively nest rules more than two levels"
            # subrule = copy(case.rrule)
            # if self.rrule._freq < HOURLY:
            #     # Days, weeks, months, years
            #     subrule._dtstart = datetime.combine(
            #         case.rrule._dtstart.date(),
            #         self.start_date.time(),
            #         tzinfo=timezone.utc,
            #     )
            # print("Adding rule", subrule)
            add_rule(case.ruleset)

        elif isinstance(case, datetime):
            add_date(case)
        elif isinstance(case, date):
            d: date = case
            self._process_special_cases(
                datetime.combine(d, self.start_date.time(), tzinfo=timezone.utc), action
            )
        elif isinstance(case, str):
            d: date = parse_date(case)
            dt: datetime = datetime.combine(
                d, self.start_date.time(), tzinfo=timezone.utc
            )
            self._process_special_cases(dt, action)
        else:
            raise TypeError(f"Cannot {action} {case}, ({type(case)})")

    def _normalize_frequency(self, freq):
        try:
            freq_str = freq.upper()
            freq = FREQ_STRS[freq_str]
        except KeyError:
            raise exc.DataGenError(
                f"Cannot accept frequency string '{freq}'. Valid strings are {tuple(FREQ_STRS.keys())}"
            )

        except Exception as e:
            raise exc.DataGenError(
                f"Cannot accept frequency string '{freq}' because {repr(e)}"
            )
        if freq in (rrule_mod.HOURLY, rrule_mod.MINUTELY, rrule_mod.SECONDLY):

            if self.next != self._next_datetime:
                raise exc.DataGenError(
                    "If frequency is a time value, `start_date` should be a datetime"
                )

        return freq

    def _normalize_weekday(self, byweekday: T.Optional[str]):
        assert byweekday

        if isinstance(byweekday, str):
            weekdays = byweekday.split(",")
        else:
            raise exc.DataGenTypeError(
                f"Wrong type for byweekday {byweekday}, {type(byweekday)}"
            )

        days = [self._parse_weekday(day) for day in weekdays]

        return days

    def _parse_weekday(self, day):
        try:
            if "(" in day:
                day, offset = self._split_weekday(day)
            else:
                offset = None
            dayconst = WEEKDAYS[day.upper().strip()]

        except (TypeError, KeyError):
            raise exc.DataGenTypeError(
                f"Do not know how to interpret {day} as a day of the week."
            )

        if offset:
            dayconst = dayconst(offset)
        return dayconst

    def _split_weekday(self, day) -> T.Tuple[str, int]:
        parts = re.match(r"\s*(?P<weekday>\w+)\((?P<offset>.+)\)\s*", day)
        if not parts:
            raise exc.DataGenSyntaxError(f"Cannot understand {day}")
        weekday = parts["weekday"]
        offset = parts["offset"]
        try:
            offset = int(offset)
        except ValueError:
            raise exc.DataGenTypeError(f"Cannot interpret {offset} as a number")
        return weekday, offset

    def __iter__(self):
        return iter(self.ruleset)

    def _next_datetime(self):
        return next(self.iterator)

    def _next_date(self):
        val: datetime = next(self.iterator)
        return val.date()


class Schedule(SnowfakeryPlugin):
    class Functions:
        @memorable
        def Event(
            self,
            freq: str,
            start_date=None,
            interval=1,
            # wkst=None,
            count=None,
            until=None,
            bysetpos=None,  # undocumented feature for now
            bymonth=None,  # undocumented feature for now
            bymonthday=None,
            byyearday=None,
            byeaster=None,
            byweekno=None,
            byweekday=None,
            byhour=None,
            byminute=None,
            bysecond=None,
            cache=False,
            exclude=None,
            include=None,
        ):
            return CalendarRule(
                freq=freq,
                start_date=start_date,
                interval=interval,
                # wkst=wkst,
                count=count,
                until=until,
                bysetpos=bysetpos,  # No requirement identified yet
                bymonth=bymonth,  # No requirement id
                bymonthday=bymonthday,
                byyearday=byyearday,
                byeaster=byeaster,
                byweekno=byweekno,
                byweekday=byweekday,
                byhour=byhour,
                byminute=byminute,
                bysecond=bysecond,
                cache=cache,
                exclude=exclude,
                include=include,
            )


def process_list_of_ints(val):
    if val is None:
        return None
    elif isinstance(val, int):
        return [val]
    elif isinstance(val, str):
        # TODO: Test what happens if this is a wrong-formatted string
        return [int(v) for v in val.split(",")]
    elif isinstance(val, collections.Sequence):
        return [int(v) for v in val]
    else:
        raise exc.DataGenTypeError(
            f"Expected a number or list of numbers, not {val} ({type(val)})"
        )
