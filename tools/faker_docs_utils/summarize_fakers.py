from pathlib import Path
import types
import typing as T

import yaml


class FakerInfo(T.NamedTuple):
    name: str
    fullname: str
    aliases: T.List[str]
    url: str
    source: str
    category: str
    doc: str
    common: bool
    sample: str


def summarize_all_fakers(faker) -> T.Sequence[FakerInfo]:
    """Summarize information about all fakers"""
    from snowfakery.utils.collections import CaseInsensitiveDict

    # get config info that can override samples etc.
    with (Path(__file__).parent / "docs_config.yml").open() as f:
        yaml_data = yaml.safe_load(f)
        common_fakes = yaml_data["common_fakes"]
        uncommon_fakes = yaml_data["uncommon_fakes"]
        ignorables = [name.lower() for name in yaml_data["ignore"]]

    faker_infos = CaseInsensitiveDict()
    for name, meth in faker.fake_names.items():
        if not isinstance(meth, types.MethodType) or name.lower() in ignorables:
            continue
        # python magic to introspect classnames, filenames, etc.
        friendly = _to_camel_case(name)
        func = meth.__func__
        doc = func.__doc__
        filename = func.__code__.co_filename
        cls = meth.__self__.__class__
        fullname = cls.__module__ + "." + cls.__name__ + "." + meth.__name__
        overrides = common_fakes.get(meth.__name__) or uncommon_fakes.get(meth.__name__)
        is_common = meth.__name__ in common_fakes

        # if it came from Faker
        if "/faker/" in filename:
            source = "faker"
            idx = filename.find("/faker/")
            url = "https://github.com/joke2k/faker/tree/master" + filename[idx:]
            parts = filename.split("/")
            while parts[-1] in ("__init__.py", "en_US"):
                del parts[-1]
            category = parts[-1]
        else:  # if it came from Snowfakery
            source = "snowfakery"
            idx = filename.find("/snowfakery/")
            url = (
                "https://github.com/SFDO-Tooling/Snowfakery/tree/main" + filename[idx:]
            )
            category = "Salesforce"

        faker_info = faker_infos.setdefault(
            friendly,
            FakerInfo(
                friendly,
                fullname,
                [],
                url,
                source,
                category,
                doc or "",
                is_common,
                overrides.get("example") if overrides else None,
            ),
        )
        faker_info.aliases.append(name)

    return faker_infos.values()


def _to_camel_case(snake_str):
    components = snake_str.split("_")
    return "".join(x.title() for x in components)
