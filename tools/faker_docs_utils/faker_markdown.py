import re
from functools import lru_cache
from pathlib import Path

from faker import Faker
from faker.config import AVAILABLE_LOCALES
from tools.faker_docs_utils.format_samples import yaml_samples_for_docstring
from tools.faker_docs_utils.summarize_fakers import get_all_fakers

from snowfakery.fakedata.fake_data_generator import FakeData

_RE_COMBINE_WHITESPACE = re.compile(r"(?<=^) +", re.MULTILINE)
_RE_STRIP_SAMPLES = re.compile(r"^\s*:sample:.*$", re.MULTILINE)
_COMMENT_LINES_THAT_LOOK_LIKE_TITLES = re.compile(r"^#", re.MULTILINE)

non_countries = ("fr_QC", "ar_AA")
AVAILABLE_LOCALES = [
    locale
    for locale in AVAILABLE_LOCALES
    if locale not in non_countries and "_" in locale
]


def strip(my_str):
    my_str = _RE_COMBINE_WHITESPACE.sub("", my_str)
    my_str = _RE_STRIP_SAMPLES.sub("", my_str).strip()
    my_str = _COMMENT_LINES_THAT_LOOK_LIKE_TITLES.sub(" #", my_str)
    my_str = my_str.replace(":example", "Example:")
    return my_str


@lru_cache(maxsize=1000)
def country_for_locale(locale: str):
    f = Faker(locale)
    return f.current_country()


def locales_as_markdown(current_locale: str):
    def format_link(locale: str):
        try:
            country_name = country_for_locale(locale)
        except (ValueError, AttributeError):
            return None
        link_text = f"{locale} : {country_name}"
        return f" - [{link_text}]({locale}.md)\n"

    other_locales = [locale for locale in AVAILABLE_LOCALES if locale != current_locale]
    links = [format_link(locale) for locale in other_locales]
    return " ".join(link for link in links if link)


def generate_markdown_for_fakers(outfile, locale):
    faker = Faker(locale)
    fd = FakeData(faker)

    all_fakers = get_all_fakers(fd)

    def output(*args, **kwargs):
        print(*args, **kwargs, file=outfile)

    output(f"# Fake Data: {locale}\n")

    output(
        f"""The basic concepts of fake data are described in
the [main docs](index.md#fake-data).

Current Locale: {locale} ({faker.current_country()})\n

Our fake data can be localized to many languages. We have
[detailed docs](https://snowfakery.readthedocs.io/en/feature-fake-data-docs/locales.html)
about the other languages.
"""
    )

    output("[TOC]\n")

    output("## Commonly Used\n")
    summarize_categories(output, [f for f in all_fakers if f.common], "", locale)
    output("## Rarely Used\n")
    summarize_categories(output, [f for f in all_fakers if not f.common], "", locale)


def summarize_categories(output, fakers, common: str, locale):
    categorized = categorize(fakers)
    for category_name, fakers in categorized.items():
        output(f"### {category_name.title()} Fakers\n")
        for faker in fakers:
            output_faker(faker.name, faker, output, locale)


def categorize(fakers):
    categories = {}
    for fakerdata in fakers:
        category = fakerdata.category
        categories.setdefault(category, [])
        categories[category].append(fakerdata)
    return {name: value for name, value in sorted(categories.items())}


def output_faker(name, data, output, locale):
    output(f"#### fake: {name}\n")
    if strip(data.doc):
        output(strip(data.doc))
        output()

    output("Aliases: ", ", ".join(data.aliases))
    output()
    link = f"[{data.source}]({data.url})"
    output("Source:", link)
    samples = yaml_samples_for_docstring(name, data.fullname, data.doc, locale)
    samples = list(filter(None, samples))
    if samples:
        output()
        output("##### Samples")
        output()
        for sample in samples:
            yaml, out = sample
            output("Recipe:\n")
            output(indent(yaml))
            output("Outputs:\n")
            output(indent(out))
    else:
        output()


def indent(yaml):
    lines = yaml.split("\n")

    def prefix(line):
        return "    " if line.strip() else ""

    lines = [prefix(line) + line for line in lines]
    return "\n".join(lines)


def generate_markdown_for_all_locales(path: Path, locales=AVAILABLE_LOCALES):
    for locale in locales:
        with Path(path, f"{locale}.md").open("w") as f:
            generate_markdown_for_fakers(f, locale)


def generate_locales_index(path: Path):
    with Path(path).open("w") as outfile:

        def output(*args, **kwargs):
            print(*args, **kwargs, file=outfile)

        locales = locales_as_markdown(None)
        if locales:
            output("## Faker Locales\n")
            output(locales)
