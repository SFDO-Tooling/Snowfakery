import re
from functools import lru_cache
from pathlib import Path
import typing as T

from yaml import dump as yaml_dump
from faker import Faker
from faker.config import AVAILABLE_LOCALES
from tools.faker_docs_utils.format_samples import (
    yaml_samples_for_docstring,
    snowfakery_output_for,
)
from .summarize_fakers import summarize_all_fakers
from .language_codes import language_codes

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


def cleanup_docstring(my_str):
    "Clean up a docstring to remove Faker-doc weirdness and excesss whitespace"
    my_str = _RE_COMBINE_WHITESPACE.sub("", my_str)
    my_str = _RE_STRIP_SAMPLES.sub("", my_str).strip()
    my_str = _COMMENT_LINES_THAT_LOOK_LIKE_TITLES.sub(" #", my_str)
    my_str = my_str.replace(":example", "\nExample:")
    my_str = my_str.replace(":param", "\nParam:")
    my_str = my_str.replace(":return", "\nReturn:")
    return my_str


@lru_cache(maxsize=1000)
def country_for_locale(locale: str):
    f = Faker(locale)
    return f.current_country()


def locales_as_markdown_links(current_locale: str, locale_list: T.List[str]):
    "Generate a list of Markdown locale links"

    def format_link(locale: str):
        try:
            country_name = country_for_locale(locale)
        except (ValueError, AttributeError):
            return None
        language = language_codes[locale.split("_")[0]]
        link_text = f"{language} as spoken in {country_name}: ({locale})"
        return f" - [{link_text}](fakedata/{locale}.md)\n"

    other_locales = [locale for locale in locale_list if locale != current_locale]
    links = [format_link(locale) for locale in other_locales]
    return " ".join(link for link in links if link)


standard_header = (Path(__file__).parent / "fakedata_header_short.md").read_text()


def generate_markdown_for_fakers(outfile, locale: str, header: str = standard_header):
    "Generate the Markdown page for a locale"
    faker = Faker(locale)
    language = language_codes[locale.split("_")[0]]
    fd = FakeData([], locale)

    all_fakers = summarize_all_fakers(fd)

    def output(*args, **kwargs):
        print(*args, **kwargs, file=outfile)

    head_md = header.format(
        locale=locale, current_country=faker.current_country(), language=language
    )
    output(
        head_md,
    )

    output("[TOC]\n")

    output("## Commonly Used\n")
    output_fakers_in_categories(output, [f for f in all_fakers if f.common], "", locale)
    output("## Rarely Used\n")
    output_fakers_in_categories(
        output, [f for f in all_fakers if not f.common], "", locale
    )


def output_fakers_in_categories(output, fakers, common: str, locale):
    """Sort fakers into named categores and then output them"""
    categorized = categorize(fakers)
    for category_name, fakers in categorized.items():
        output(f"### {category_name.title()} Fakers\n")
        for faker in fakers:
            output_faker(faker.name, faker, output, locale)


def categorize(fakers):
    "Sort fakers based on their categories (what module they came from)"
    categories = {}
    for fakerdata in fakers:
        category = fakerdata.category
        categories.setdefault(category, [])
        categories[category].append(fakerdata)
    return {name: value for name, value in sorted(categories.items())}


def gather_samples(name, data, locale):
    if data.sample:  # I already have a sample, no need to generate one
        if locale and locale != "en_US":
            locale_header = [{"var": "snowfakery_locale", "value": locale}]
            sample = locale_header + data.sample
        else:
            sample = data.sample
        example = yaml_dump(sample, sort_keys=False)
        samples = [snowfakery_output_for(data.name, example, example)]
    else:  # need to generate a sample from scratch
        samples = yaml_samples_for_docstring(name, data.fullname, data.doc, locale)
    return list(filter(None, samples))


def output_faker(name: str, data: str, output: callable, locale: str):
    """Output the data relating to a particular faker"""
    samples = gather_samples(name, data, locale)
    # if there isn't at least one sample, don't publish
    if not samples:
        return

    output(f"#### fake: {name}\n")
    cleaned_docstring = cleanup_docstring(data.doc)
    if cleaned_docstring:
        output(cleaned_docstring)
        output()

    output("Aliases: ", ", ".join(data.aliases))
    output()
    link = f"[{data.source}]({data.url}) : {data.fullname}"
    output("Source:", link)

    if samples:
        output()
        for sample in samples:
            yaml, out = sample

            output("Recipe:\n")
            output(indent(yaml))
            output("Outputs:\n")
            output(indent(out))
    else:
        output()


def indent(yaml: str):
    """Add indents to yaml"""
    lines = yaml.split("\n")

    def prefix(line):
        return "    " if line.strip() else ""

    lines = [prefix(line) + line for line in lines]
    return "\n".join(lines)


def generate_markdown_for_all_locales(path: Path, locales=None):
    "Generate markdown file for each listed locale. None means all locales"
    locales = locales or AVAILABLE_LOCALES
    for locale in locales:
        with Path(path, f"{locale}.md").open("w") as f:
            print(f.name)
            generate_markdown_for_fakers(f, locale)


def generate_locales_index(path: Path, locales_list: T.List[str]):
    "Generate markdown index including listed locales. None means all locales"
    locales_list = locales_list or AVAILABLE_LOCALES
    with Path(path).open("w") as outfile:

        def output(*args, **kwargs):
            print(*args, **kwargs, file=outfile)

        locales = locales_as_markdown_links(None, locales_list)
        if locales:
            output("## Fake Data Locales\n")
            output(
                "Learn more about Snowfakery localization in the [Fake Data Tutorial](fakedata.md#localization)\n"
            )
            output(locales)
