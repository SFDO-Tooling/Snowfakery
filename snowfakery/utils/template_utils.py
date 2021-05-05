from functools import lru_cache
from typing import Sequence
import string

from faker import Faker
from jinja2 import Template
from snowfakery.fakedata.fake_data_generator import FakeData


class StringGenerator:
    """Sometimes in templates you want a reference to a variable to
    call a function.

    For example:

    >>> x = template_utils.StringGenerator(datetime.today().isoformat)
    >>> print(f"{x}")
    2019-09-23T11:49:01.994453

    >>> x = template_utils.StringGenerator(lambda:str(random.random()))
    >>> print(f"{x}")
    0.795273959965055
    >>> print(f"{x}")
    0.053061903749985206
    """

    def __init__(self, func):
        self.func = func

    def __str__(self):
        return str(self.func())

    def __call__(self, *args, **kwargs):
        return self.func(*args, **kwargs)

    def __add__(self, other):
        return str(self) + str(other)

    def __radd__(self, other):
        return str(other) + str(self)


class FakerTemplateLibrary:
    """A Jinja template library to add the faker.xyz objects to templates"""

    def __init__(self, faker_providers: Sequence[object], locale=None):
        self.locale = locale

        # TODO: Push this all down into FakeData
        faker = Faker(self.locale, use_weighting=False)
        for provider in faker_providers:
            faker.add_provider(provider)

        self.fake_data = FakeData(faker)

    def _get_fake_data(self, name):
        return self.fake_data._get_fake_data(name)

    def __getattr__(self, name):
        return StringGenerator(
            lambda *args, **kwargs: self.fake_data._get_fake_data(name, *args, **kwargs)
        )


Template = lru_cache(512)(Template)


number_chars = set(string.digits + ".")


def look_for_number(arg):
    looks_like_float = False
    if len(arg) == 0:
        return arg
    for char in arg:
        if char not in number_chars:
            return arg
        if char == ".":
            if looks_like_float:
                # we already saw a ".", so this string must be
                # of the form ###.###.### like a euro-phone #
                return arg
            else:
                looks_like_float = True
    if looks_like_float:
        return float(arg)
    else:
        return int(arg)
