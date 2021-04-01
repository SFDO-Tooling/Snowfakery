from faker import Faker
from datetime import date


class FakeFaker:
    def add_provider(self, *args, **kwargs):
        pass

    def format(self, name, *args, **kwargs):
        if hasattr(self, name):
            return getattr(self, name)(*args, **kwargs)
        return "Hodor Hodor"

    def country_code(self, *args, representation=None):
        if representation == "alpha-2":
            return "CA"
        else:
            return "country_code Hodor"

    def date(self, *args, pattern=None, end_datetime=None):
        the_date = date(year=1999, month=3, day=8)
        if pattern:
            return the_date.strftime(pattern)
        else:
            return the_date

    def date_between(self, start_date, end_date):
        from snowfakery.template_funcs import _try_parse_date

        start_date = _try_parse_date(start_date)

        return Faker().date_between(start_date=start_date, end_date=start_date)


class FakeData(Faker):
    pass


def make_faker(
    locale=None, deterministic_fake=False, use_weighting=False, *args, **kwargs
):
    if deterministic_fake:
        return FakeFaker()
    else:
        return FakeData(locale, *args, use_weighting=use_weighting, **kwargs)
