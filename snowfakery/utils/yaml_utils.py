from yaml import SafeDumper


class SnowfakeryDumper(SafeDumper):
    pass


def hydrate(cls, data):
    obj = cls.__new__(cls)
    obj.__setstate__(data)
    return obj
