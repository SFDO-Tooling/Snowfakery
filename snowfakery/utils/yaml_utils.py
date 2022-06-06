from typing import Callable
from yaml import SafeDumper, SafeLoader
from yaml.representer import Representer
from collections import defaultdict


class SnowfakeryContinuationDumper(SafeDumper):
    pass


SnowfakeryContinuationDumper.add_representer(
    defaultdict, SnowfakeryContinuationDumper.represent_dict
)


def hydrate(cls, data):
    obj = cls.__new__(cls)
    obj.restore_from_continuation(data)
    return obj


# Evaluate whether its cleaner for functions to bypass  register_for_continuation
# and go directly to SnowfakeryContinuationDumper.add_representer.
#
#


def represent_continuation(dumper: SnowfakeryContinuationDumper, data):
    if isinstance(data, dict):
        return Representer.represent_dict(dumper, data)
    else:
        return Representer.represent_object(dumper, data)


def register_for_continuation(cls, dump_transformer: Callable = lambda x: x):
    SnowfakeryContinuationDumper.add_representer(
        cls, lambda self, data: represent_continuation(self, dump_transformer(data))
    )
    SafeLoader.add_constructor(
        f"tag:yaml.org,2002:python/object/apply:{cls.__module__}.{cls.__name__}",
        lambda loader, node: cls._from_continuation(
            loader.construct_mapping(node.value[0])
        ),
    )
