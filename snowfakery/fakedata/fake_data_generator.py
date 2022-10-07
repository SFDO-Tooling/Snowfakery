import random
import typing as T
import datetime
from difflib import get_close_matches
from itertools import product

import dateutil
from faker import Faker, Generator

from snowfakery.plugins import PluginContext
import snowfakery.data_gen_exceptions as exc

# .format language doesn't allow slicing. :(
first_name_patterns = ("{firstname}", "{firstname[0]}", "{firstname[0]}{firstname[1]}")
first_name_separators = ("", ".", "-", "_", "+")
year_patterns = ("{year}", "{year[2]}{year[3]}", "{year[3]}", "")

email_templates = [
    f"{first_name}{first_name_separator}{{lastname}}{year}@{{domain}}"
    for first_name, first_name_separator, year in product(
        first_name_patterns, first_name_separators, year_patterns
    )
]

this_year = datetime.datetime.today().year
DateLike = T.Union[datetime.date, datetime.datetime, datetime.timedelta, str, int]
TimeZoneAsRelDelta = T.Union[dateutil.relativedelta.relativedelta, T.Literal[False]]
UTCAsRelDelta = dateutil.relativedelta.relativedelta(hours=0)


class FakeNames(T.NamedTuple):
    f: Faker
    faker_context: PluginContext = None

    # "matching" allows us to turn off the behaviour of
    # trying to incorporate one field into another if we
    # need to.
    def user_name(self, matching: bool = True):
        "Globally unique Salesforce-style username in the form of an email address"
        domain = self.f.hostname()
        already_created = self._already_have(("firstname", "lastname"))
        if matching and all(already_created):
            namepart = f"{already_created[0]}.{already_created[1]}_{self.f.uuid4()}"
        else:
            namepart = f"{self.f.first_name()}_{self.f.last_name()}_{self.f.uuid4()}"

        namepart_max_len = 80 - (len(domain) + 1)
        namepart = namepart[0:namepart_max_len]
        return f"{namepart}@{domain}"

    def alias(self):
        """Salesforce-style 8-character alias: really an 8 char-truncated firstname.
        Not necessarily unique, but likely to be unique if you create small
        numbers of them."""
        return self.f.first_name()[0:8]

    def email(self, matching: bool = True):
        """Email address using one of the "example" domains"""
        already_created = self._already_have(("firstname", "lastname"))
        if matching and all(already_created):
            template = random.choice(email_templates)

            return template.format(
                firstname=already_created[0].ljust(2, "_"),
                lastname=already_created[1],
                domain=self.f.safe_domain_name(),
                year=str(random.randint(this_year - 80, this_year - 10)),
            )
        return self.f.ascii_safe_email()

    def realistic_maybe_real_email(self):
        """Like fake: email except that the email domain may be real and therefore
        the email address itself may be real. Use with caution, you might
        accidentally email strangers!!!
        """
        return self.f.email()

    def _already_have(self, names: T.Sequence[str]):
        """Get a list of field values that we've already generated"""
        already_created = self.faker_context.local_vars()
        vals = [already_created.get(name) for name in names]

        # if we ever need to use this function in a context where Unicode
        # is okay, here's how to implement that:
        # cleanup_func = replace_unicode_strings_with_None if must_be_ascii else NOOP

        vals = [replace_unicode_strings_with_None(val) for val in vals]

        return vals

    def state(self):
        """Return a state, province or other appropriate administrative unit"""
        return self.f.administrative_unit()

    def postalcode(self):
        """Return whatever counts as a postalcode for a particular locale"""
        return self.f.postcode()

    def date_time_between(
        self,
        start_date: DateLike = "-30y",
        end_date: DateLike = "now",
        timezone: TimeZoneAsRelDelta = UTCAsRelDelta,
    ) -> datetime.datetime:
        timezone = _normalize_timezone(timezone)
        return self.f.date_time_between(start_date, end_date, timezone)

    date_time_between_dates = date_time_between

    def future_datetime(
        self,
        end_date: DateLike = "+30d",
        timezone: TimeZoneAsRelDelta = UTCAsRelDelta,
    ) -> datetime.datetime:
        timezone = _normalize_timezone(timezone)
        return self.f.future_datetime(end_date, timezone)

    def iso8601(
        self,
        timezone: TimeZoneAsRelDelta = UTCAsRelDelta,
        end_datetime: DateLike = None,
    ) -> str:
        timezone = _normalize_timezone(timezone)
        return self.f.iso8601(
            timezone,
            end_datetime,
        )

    date_time = datetime = date_time_between

    # These faker types are not available in Snowfakery
    # because they are redundant
    date_time_this_year = NotImplemented
    date_time_this_year = NotImplemented
    date_time_this_month = NotImplemented
    date_time_ad = NotImplemented
    date_time_this_century = NotImplemented
    date_time_this_decade = NotImplemented


def _normalize_timezone(timezone=None):
    if timezone in (None, False):
        return None
    elif timezone is UTCAsRelDelta:
        return datetime.timezone.utc
    else:
        if not isinstance(timezone, dateutil.relativedelta.relativedelta):
            raise exc.DataGenError(  # pragma: no cover
                f"`timezone` should be a `relativedelta`, not `{type(timezone).__name__}`: {timezone}"
            )
        return datetime.timezone(
            datetime.timedelta(hours=timezone.hours, minutes=timezone.minutes)
        )


# we will use this to exclude Faker's internal book-keeping methods
# from our faker interface
faker_class_attrs = set(dir(Faker)).union((dir(Generator)))


class FakeData:
    """Wrapper for Faker which adds Salesforce names and case insensitivity."""

    def __init__(
        self,
        faker_providers: T.Sequence[object],
        locale: T.Optional[str] = None,
        faker_context: T.Optional[PluginContext] = None,
    ):
        # access to persistent state
        self.faker_context = faker_context

        faker = Faker(locale, use_weighting=False)
        for provider in faker_providers:
            faker.add_provider(provider)

        fake_names = FakeNames(faker, faker_context)

        def no_underscore_name(name):
            return name.lower().replace("_", "")

        def obj_to_func_list(obj: object, canonicalizer: T.Callable, ignore_list: set):
            return {
                canonicalizer(name): getattr(obj, name)
                for name in dir(obj)
                if not name.startswith("_") and name not in ignore_list
            }

        # canonical form of names is lower-case, no underscores
        # include faker names with underscores in case of ab_c/a_bc clashes
        # include faker names with no underscores to emulate salesforce
        # include snowfakery names defined above
        self.fake_names = {
            **obj_to_func_list(faker, str.lower, faker_class_attrs),
            **obj_to_func_list(faker, no_underscore_name, faker_class_attrs),
            # in case of conflict, snowfakery names "win" over Faker names
            **obj_to_func_list(fake_names, str.lower, set()),
            **obj_to_func_list(fake_names, no_underscore_name, set()),
        }

    def _get_fake_data(self, origname, *args, **kwargs):
        local_faker_vars = self.faker_context.local_vars()

        # faker names are all lower-case
        name = origname.lower()

        meth = self.fake_names.get(name, NotImplemented)

        if meth != NotImplemented:
            ret = meth(*args, **kwargs)
            local_faker_vars[name.replace("_", "")] = ret
            return ret

        msg = f"No fake data type named {origname}."
        all_fake_names = [k for k, v in self.fake_names.items() if v != NotImplemented]
        match_list = get_close_matches(name, all_fake_names, n=1)
        if match_list:
            msg += f" Did you mean {match_list[0]}"
        raise AttributeError(msg)


def translate(x):
    if chr(x).isalnum():
        return x
    else:
        return None


REMOVE_WEIRD_CHARS = {x: translate(x) for x in range(0, 128)}


def replace_unicode_strings_with_None(val):
    if type(val) == str:
        if not val.isascii():
            return None
        return val.translate(REMOVE_WEIRD_CHARS)
    return val
