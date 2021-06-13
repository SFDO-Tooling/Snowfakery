from pathlib import Path
import types
import typing as T

import yaml


def get_all_fakers(faker):
    from snowfakery.utils.collections import CaseInsensitiveDict

    with (Path(__file__).parent / "docs_config.yml").open() as f:
        common_fakes = yaml.safe_load(f)["common_fakes"]

    faker_infos = CaseInsensitiveDict()
    for name, meth in faker.fake_names.items():
        if not isinstance(meth, types.MethodType):
            continue
        friendly = _to_camel_case(name)
        func = meth.__func__
        doc = func.__doc__
        filename = func.__code__.co_filename
        cls = meth.__self__.__class__
        fullname = cls.__module__ + "." + cls.__name__ + "." + meth.__name__
        is_common = meth.__name__ in common_fakes
        if "/faker/" in filename:
            source = "faker"
            idx = filename.find("/faker/")
            url = "https://github.com/joke2k/faker/tree/master" + filename[idx:]
            parts = filename.split("/")
            while parts[-1] in ("__init__.py", "en_US"):
                del parts[-1]
            category = parts[-1]
        else:
            source = "snowfakery"
            idx = filename.find("/snowfakery/")
            url = (
                "https://github.com/SFDO-Tooling/Snowfakery/tree/main" + filename[idx:]
            )
            category = "Salesforce"

        faker_info = faker_infos.setdefault(
            friendly,
            FakerInfo(
                friendly, fullname, [], url, source, category, doc or "", is_common
            ),
        )
        faker_info.aliases.append(name)

    return faker_infos.values()


class FakerInfo(T.NamedTuple):
    name: str
    fullname: str
    aliases: T.List[str]
    url: str
    source: str
    category: str
    doc: str
    common: bool


def _to_camel_case(snake_str):
    components = snake_str.split("_")
    return "".join(x.title() for x in components)
