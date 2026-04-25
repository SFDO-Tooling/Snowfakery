"""Pin the PEP 649 (Python 3.14) annotation-resolution regression for FakeNames."""
import inspect
import datetime as dt

from faker import Faker

from snowfakery.fakedata.fake_data_generator import FakeNames


def test_inspect_signature_works_on_date_time_between():
    fn = FakeNames(f=Faker())
    sig = inspect.signature(fn.date_time_between)
    assert sig.return_annotation is dt.datetime, sig.return_annotation


def test_fn_datetime_alias_still_callable():
    fn = FakeNames(f=Faker())
    assert fn.datetime.__name__ == "date_time_between"
    result = fn.datetime()
    assert isinstance(result, dt.datetime)
