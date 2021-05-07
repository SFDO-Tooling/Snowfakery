from difflib import get_close_matches
from faker import Faker
import typing as T


class FakeNames(T.NamedTuple):
    f: Faker

    def Username(self):
        return f"{self.f.first_name()}_{self.f.last_name()}_{self.f.uuid4()}@{self.f.hostname()}"

    def Alias(self):
        return self.f.first_name()[0:8]

    def FirstName(self):
        return self.f.first_name()

    def LastName(self):
        return self.f.last_name()

    def Email(self):
        return self.f.ascii_safe_email()

    def RealisticMaybeRealEmail(self):
        return self.f.email()


class FakeData:
    """Wrapper Faker which adds Salesforce names and case insensitivity."""

    def __init__(self, faker: Faker):
        self.faker = faker
        self.fake_names = FakeNames(faker)

        # canonical form of names is lower-case
        self._lowers = {
            v.lower(): v for v in dir(self.fake_names) if not v.startswith("_")
        }

    def _get_fake_data(self, origname, *args, **kwargs):
        # faker names are all lower-case
        name = origname.lower()
        if name in self._lowers:
            meth = getattr(self.fake_names, self._lowers[name])
            return meth(*args, **kwargs)
        else:
            try:
                # TODO: look for FooBar as foo_bar
                return getattr(self.faker, name)()
            except AttributeError:
                pass

        msg = f"No fake data type named {origname}."
        match_list = get_close_matches(name, self._lowers.values(), n=1)
        if match_list:
            msg += f" Did you mean {match_list[0]}"
        raise AttributeError(msg)
