import string
import random
from faker.providers import BaseProvider


class Provider(BaseProvider):
    def ThreeLetterAcronym(self):
        alpha = string.ascii_uppercase
        letters = random.choices(alpha, k=3)
        acronym = "".join(letters)
        return acronym
