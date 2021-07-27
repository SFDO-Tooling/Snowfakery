import ast
import yaml

from io import StringIO
from collections import OrderedDict
from unittest.mock import MagicMock

from snowfakery import generate_data

from . import docstring

# known code gen issues. ignore them.
IGNORE_ERRORS = set(("uuid4", "randomchoices", "randomelement", "randomelements"))


def samples_from_docstring(fullname, docstring_data):
    """Convert a Faker-style docstring into a Snowfaery sample"""
    lines = docstring_data.split("\n")
    lines = [line.strip() for line in lines]
    docstrings = docstring.ProviderMethodDocstring(
        app=MagicMock(),
        what="method",
        name=fullname,
        obj=MagicMock,
        options=MagicMock(),
        lines=lines,
    )
    return docstrings._samples


def simplify(arg):
    """Simplify Faker arg-types. e.g. tuples become lists. OrdereDicts become dicts"""
    fieldname = arg._fields[0]
    out = getattr(arg, fieldname)

    # primitives are fine
    if isinstance(out, (str, int, float, bool)):
        return out

    # simplify tuples to lists, and simplify the contents
    if isinstance(out, (list, tuple)):
        args = [simplify(a) for a in out]
        return type(out)(args)

    # simplify OrderedDicts to dicts, and simplify the contents
    if isinstance(out, (OrderedDict, dict)):
        return {name: simplify(value) for name, value in dict(out).items()}
    raise TypeError(type(out), out)


def extract_keywords(kwargstr):
    """Reverse engineer the params from a Snowfakery faker by using the Python parser"""
    fake_python = f"Func({kwargstr})"
    tree = ast.parse(fake_python, mode="eval")
    kwds = {arg.arg: simplify(arg.value) for arg in tree.body.keywords}
    return kwds


def reformat_yaml(yaml_data):
    """Normalize YAML to a common format"""
    data = yaml.safe_load(yaml_data)
    return yaml.dump(data, sort_keys=False)


def yaml_samples_for_docstring_sample(name, sample, locale):
    """Try to generate Snowfakery input and output for a faker."""
    try:
        return _yaml_samples_for_docstring_sample_inner(name, sample, locale)
    except Exception as e:
        print("Cannot generate sample from docstring", sample, str(e)[0:100])
        raise e


def _yaml_samples_for_docstring_sample_inner(name, sample, locale):
    """Try to generate Snowfakery input and output for a faker."""
    try:
        kwds = extract_keywords(sample.kwargs)
    except Exception as e:
        if name.lower() not in IGNORE_ERRORS:
            IGNORE_ERRORS.add(name.lower())
            print("Cannot extract keywords", name, sample, str(e)[0:100])
        return None

    name = name.split(".")[-1]
    return yaml_sample(name, kwds, sample.kwargs, locale)


def yaml_sample(name, kwds, kw_example, locale):
    """Generate Snowfakery yaml input and output"""
    if kwds:
        inline_example = f"fake.{name}({kw_example})"
        block_example = {f"fake.{name}": kwds}
    else:
        inline_example = f"fake.{name}"
        block_example = {"fake": name}

    inline_example = "${{" + inline_example + "}}"

    if ":" in inline_example:
        inline_example = f'"{inline_example}"'

    single_part_example = f"""
    - object: SomeObject
      fields:
        formula_field_example: {inline_example}"""

    if locale:
        locale_decl = f"""
    - var: snowfakery_locale
      value: {locale}
    """
        single_part_example = locale_decl + single_part_example
    try:
        two_part_example = (
            single_part_example
            + f"""
        block_field_example: {block_example}"""
        )

        two_part_example = reformat_yaml(two_part_example)
        single_part_example = reformat_yaml(single_part_example)
    except Exception as e:
        print("CANNOT PARSE")
        print(two_part_example, single_part_example)
        print(str(e)[0:100])
        raise

    return snowfakery_output_for(name, two_part_example, single_part_example)


def snowfakery_output_for(name, primary_example, secondary_example):
    """Generate the Snowfakery output for some YAML

    Attempt to generate a two-part example, but fall back to single
    or nothing if worse comes to worst."""
    output = None
    exception = None

    for yaml_data in [primary_example, secondary_example]:
        with StringIO() as s:
            try:
                generate_data(StringIO(yaml_data), output_file=s, output_format="txt")
                output = s.getvalue()
                exception = None
            except Exception as e:
                exception = e

    if exception and name.lower() not in IGNORE_ERRORS:
        print(f"Cannot generate sample for {name}: {str(exception)[0:80]}")
        IGNORE_ERRORS.add(name.lower())

    if output:
        return yaml_data, output


def default_yaml_sample(name, locale):
    return yaml_sample(name, None, None, locale)


def yaml_samples_for_docstring(name, fullname, docstring_data, locale=None):
    """Generate example for all samples associated wth a docstring"""
    sample_objs = samples_from_docstring(fullname, docstring_data)

    output = [
        yaml_samples_for_docstring_sample(name, sample, locale)
        for sample in sample_objs
    ]
    if not output:
        output = [default_yaml_sample(name, locale)]
    return output
