import faker.providers
from faker import Faker


f = Faker()


# TODO: Use locale
# https://github.com/joke2k/faker/issues/1427
class Provider(faker.providers.BaseProvider):
    """Provider for Faker which adds fake microservice names."""

    def Username(self):
        return (
            f.first_name() + "_" + f.last_name() + "_" + f.uuid4() + "@" + f.hostname()
        )

    def Alias(self):
        return f.first_name()[0:8]

    def FirstName(self):
        return f.first_name()

    def LastName(self):
        return f.last_name()

    username = Username
    alias = Alias
