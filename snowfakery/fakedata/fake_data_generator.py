from difflib import get_close_matches
import typing as T

from faker import Faker, Generator


class FakeNames(T.NamedTuple):
    f: Faker

    def user_name(self):
        "Salesforce-style username in the form of an email address"
        return f"{self.f.first_name()}_{self.f.last_name()}_{self.f.uuid4()}@{self.f.hostname()}"

    def alias(self):
        """Salesforce-style 8-character alias: really an 8 char-truncated firstname.
        Not necessarily unique, but likely to be unique if you create small
        numbers of them."""
        return self.f.first_name()[0:8]

    def email(self):
        """Email address using one of the "example" domains"""
        return self.f.ascii_safe_email()

    def realistic_maybe_real_email(self):
        """Like fake: email except that the email domain may be real and therefore
        the email address itself may be real. Use with caution, you might
        accidentally email strangers!!!
        """
        return self.f.email()

    def state(self):
        """Return a state, province or other appropriate administrative unit"""
        return self.f.administrative_unit()

    def postalcode(self):
        """Return whatever counts as a postalcode for a particular locale"""
        return self.f.postcode()


# we will use this to exclude Faker's internal book-keeping methods
# from our faker interface
faker_class_attrs = set(dir(Faker)).union((dir(Generator)))


class FakeData:
    """Wrapper for Faker which adds Salesforce names and case insensitivity."""

    def __init__(self, faker: Faker):
        fake_names = FakeNames(faker)
        self.faker = faker

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
