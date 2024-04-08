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


def is_datetime(dt: str) -> bool:
    """Does a string look like a `datetime`?"""
    return bool(set(dt).intersection(" TZ+:"))


OptionalDateTimeLike = T.Union[str, date, datetime, None]
SeqOfIntsLike = T.Union[str, int, T.Sequence[int], None]
CalendarException = T.Union[
    T.Sequence[T.Union["CalendarRule", OptionalDateTimeLike]],
    "CalendarRule",
    OptionalDateTimeLike,
]


class CalendarRule(PluginResultIterator):
    """Generates calendar events"""

    iterator: T.Any  # Actually T.Union[T.Iterator[date],T.Iterator[ datetime]]

    def __init__(
        self,
        freq: str,
        start_date: OptionalDateTimeLike = None,
        interval: int = 1,
        count: T.Optional[int] = None,
        until: OptionalDateTimeLike = None,
        bysetpos: SeqOfIntsLike = None,  # undocumented feature, for now
        bymonth: SeqOfIntsLike = None,
        bymonthday: SeqOfIntsLike = None,
        byyearday: SeqOfIntsLike = None,
        byeaster: SeqOfIntsLike = None,  # undocumented feature for now
        byweekno: SeqOfIntsLike = None,  # undocumented feature for now
        byweekday: T.Optional[str] = None,
        byhour: SeqOfIntsLike = None,
        byminute: SeqOfIntsLike = None,
        bysecond: SeqOfIntsLike = None,
        cache: bool = False,  # undocumented feature for now
        exclude: CalendarException = None,
        include: CalendarException = None,
        use_undocumented_features: bool = False,
    ):
        # Certain features can only be used if you opt-in to use_undocumented_features
        self._check_undocumented_features(
            use_undocumented_features, bysetpos, byeaster, cache, byweekno
        )

        # Normalize and save the start_date
        self.start_date, precision = self._normalize_start_date(start_date)

        self._set_output_datetype_date_or_datetime(precision)

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
        byweekno = process_list_of_ints(bysecond)

        until = self._normalize_until(until)

        freq = self._normalize_frequency(freq)

        if byweekday:
            byweekday_normalized = self._normalize_weekday(byweekday)
        else:
            byweekday_normalized = None

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
            byweekday=byweekday_normalized,
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

    def _check_undocumented_features(
        self,
        use_undocumented_features: bool,
        bysetpos: SeqOfIntsLike,
        byeaster: SeqOfIntsLike,
        cache: bool,
        byweekno: SeqOfIntsLike,
    ) -> None:
        """Require opt-in for undocumented features"""
        if (not use_undocumented_features) and any(
            [bysetpos, byeaster, cache, byweekno]
        ):
            raise exc.DataGenValueError(
                "That feature is undocumented and unsupported. "
                "Use the `use_undocumented_features: True` argument to use it regardless."
            )

    def _normalize_start_date(
        self, start_date: OptionalDateTimeLike
    ) -> T.Tuple[datetime, type]:
        """Normalize the start-date to datetime

        But return a type that keeps track of its original type"""

        if isinstance(start_date, str):
            precision = datetime if is_datetime(start_date) else date
            start_date = parse_datetimespec(start_date)
            assert start_date.tzinfo
        elif isinstance(start_date, datetime):
            precision = datetime
        elif isinstance(start_date, date):
            start_date = datetime.combine(
                start_date, time(hour=0, minute=0, second=0, tzinfo=timezone.utc)
            )
            precision = date
        elif not start_date:
            start_date = datetime.now()
            precision = datetime
        else:  # pragma: no cover
            raise TypeError(
                f"`start_date` ({start_date}) is of unknown type {type(start_date)}"
            )
        if not start_date.tzinfo:
            start_date = start_date.replace(tzinfo=timezone.utc)
        assert precision in (date, datetime)

        return start_date, precision

    def _normalize_until(self, until: OptionalDateTimeLike) -> T.Optional[datetime]:
        """Normalize until value to datetime or None"""
        if not until:
            return None

        if isinstance(until, str):
            if is_datetime(until):
                until = parse_datetimespec(until)
            else:
                until = datetime.combine(parse_date(until), self.start_date.time())

        elif isinstance(until, date):
            until = datetime.combine(until, self.start_date.time(), tzinfo=timezone.utc)

        else:
            raise exc.DataGenTypeError(
                f"`until` parameter ({until}) is of unexpected type {until}"
            )

        return until.replace(tzinfo=timezone.utc)

    def _set_output_datetype_date_or_datetime(self, precision: type) -> None:
        """Depending on the precision requested, generate the right kinds of records"""
        assert precision in (date, datetime)
        if precision is date:
            self.next = self._next_date  # type: ignore
        elif precision is datetime:
            self.next = self._next_datetime  # type: ignore
        else:  # pragma: no cover
            assert False, "Should be unreachable"

    def _process_special_cases(
        self,
        case: CalendarException,
        action: T.Literal["include", "exclude"],
    ) -> None:
        """Process inclusions and exclusions"""
        if action == "exclude":
            # https://dateutil.readthedocs.io/en/stable/rrule.html#dateutil.rrule.rruleset.exrule
            add_rule = self.ruleset.exrule
            # https://dateutil.readthedocs.io/en/stable/rrule.html#dateutil.rrule.rruleset.exdate
            add_date = self.ruleset.exdate
        elif action == "include":
            # https://dateutil.readthedocs.io/en/stable/rrule.html#dateutil.rrule.rruleset.rrule
            add_rule = self.ruleset.rrule
            # https://dateutil.readthedocs.io/en/stable/rrule.html#dateutil.rrule.rruleset.rdate
            add_date = self.ruleset.rdate
        else:  # pragma: no cover   -   Should be unreachable
            assert action in ("include", "exclude"), "Bad action!"
            raise NotImplementedError("Bad action!")

        if isinstance(case, (list, tuple)):
            for case in case:
                self._process_special_cases(case, action)
        elif isinstance(case, CalendarRule):
            add_rule(T.cast(T.Any, case.ruleset))

        elif isinstance(case, datetime):
            add_date(case)
        elif isinstance(case, date):
            d: date = case
            self._process_special_cases(
                datetime.combine(d, self.start_date.time(), tzinfo=timezone.utc), action
            )
        elif isinstance(case, str):
            d2: date = parse_date(case)
            dt: datetime = datetime.combine(
                d2, self.start_date.time(), tzinfo=timezone.utc
            )
            self._process_special_cases(dt, action)
        else:  # pragma: no cover
            raise TypeError(f"Cannot {action} {case}, ({type(case)})")

    def _normalize_frequency(self, freq: str):
        """Normalize frequency string to dateutil type"""
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

    def _normalize_weekday(
        self, byweekday: T.Optional[str]
    ) -> T.List[rrule_mod.weekday]:
        """Normalize weekday string to dateutil types"""
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
        """Parse the weekday syntax like MO(+3) and WE(-2) and create dateutil datatypes"""
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
        """Parse the weekday syntax like MO(+3) and WE(-2)"""
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

    def __iter__(self) -> T.Union[T.Iterator[datetime], T.Iterator[date]]:
        return iter(self.ruleset)

    def next(self) -> None:  # pragma: no cover
        """This method is never called.

        It is replaced at runtime by _next_datetime or _next_date"""
        raise NotImplementedError("next is not implemented")

    def _next_datetime(self) -> datetime:
        return next(self.iterator)

    def _next_date(self) -> date:
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


def process_list_of_ints(val: SeqOfIntsLike) -> T.Optional[T.List[int]]:
    if val is None:
        return None
    elif isinstance(val, int):
        return [val]
    elif isinstance(val, str):
        return [int(v) for v in val.split(",")]
    elif isinstance(val, (list, tuple)):
        return [int(v) for v in val]
    else:
        raise exc.DataGenTypeError(
            f"Expected a number or list of numbers, not {val} ({type(val)})"
        )
