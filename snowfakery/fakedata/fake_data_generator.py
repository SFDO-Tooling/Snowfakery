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


# we will use this to exclude Faker's internal book-keeping methods
# from our faker interface
faker_class_attrs = set(dir(Faker))


class FakeData:
    """Wrapper for Faker which adds Salesforce names and case insensitivity."""

    def __init__(self, faker: Faker):
        fake_names = FakeNames(faker)

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
            **obj_to_func_list(
                faker, lambda x: x.lower().replace("_", ""), faker_class_attrs
            ),
            # in case of conflict, snowfakery names "win" over Faker names
            **obj_to_func_list(fake_names, str.lower, set()),
        }

    def _get_fake_data(self, origname, *args, **kwargs):
        # faker names are all lower-case
        name = origname.lower()

        meth = self.fake_names.get(name)

        if meth:
            return meth(*args, **kwargs)

        msg = f"No fake data type named {origname}."
        match_list = get_close_matches(name, self.fake_names.keys(), n=1)
        if match_list:
            msg += f" Did you mean {match_list[0]}"
        raise AttributeError(msg)
