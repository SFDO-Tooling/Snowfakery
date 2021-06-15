import ast
import yaml

from io import StringIO
from collections import OrderedDict
from unittest.mock import MagicMock

from snowfakery import generate_data

from . import docstring


def samples_from_docstring(fullname, docstring_data):
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
    fieldname = arg._fields[0]
    out = getattr(arg, fieldname)
    if isinstance(out, (str, int, float, bool)):
        return out
    if isinstance(out, (list, tuple)):
        args = [simplify(a) for a in out]
        return type(out)(args)
    if isinstance(out, (OrderedDict, dict)):
        return {name: simplify(value) for name, value in dict(out).items()}
    raise TypeError(type(out), out)


def extract_keywords(kwargstr):
    fake_python = f"Func({kwargstr})"
    tree = ast.parse(fake_python, mode="eval")
    kwds = {arg.arg: simplify(arg.value) for arg in tree.body.keywords}
    return kwds


def reformat_yaml(yaml_data):
    data = yaml.safe_load(yaml_data)
    return yaml.dump(data, sort_keys=False)


def yaml_samples_for_docstring_sample(name, sample, locale):
    try:
        return yaml_samples_for_docstring_sample_inner(name, sample, locale)
    except Exception as e:
        print("Cannot generate sample for", sample, str(e)[0:100])
        raise e


def yaml_samples_for_docstring_sample_inner(name, sample, locale):
    try:
        kwds = extract_keywords(sample.kwargs)
    except Exception as e:
        print("Cannot extract keywords", sample, str(e)[0:100])
        return None

    name = name.split(".")[-1]
    return yaml_sample(name, kwds, sample.kwargs, locale)


def yaml_sample(name, kwds, kw_example, locale):
    if kwds:
        inline_example = f"fake.{name}({kw_example})"
        block_example = {f"fake.{name}": kwds}
    else:
        inline_example = f"fake.{name}"
        block_example = {"fake": name}

    inline_example = "${{" + inline_example + "}}"

    if ":" in inline_example:
        inline_example = f'"{inline_example}"'

    yaml_data = f"""
    - object: SomeObject
      fields:
        formula_field_example: {inline_example}
        block_field_example: {block_example}"""

    if locale:
        locale_decl = f"""
    - var: snowfakery_locale
      value: {locale}
    """
        yaml_data = locale_decl + yaml_data
    try:
        yaml_data = reformat_yaml(yaml_data)
    except Exception as e:
        print("CANNOT PARSE")
        print(yaml_data)
        print(str(e)[0:100])
        raise

    return snowfakery_output_for(yaml_data)


def snowfakery_output_for(yaml_data):
    with StringIO() as s:
        try:
            generate_data(StringIO(yaml_data), output_file=s, output_format="txt")
        except Exception as e:
            print("Cannot generate")
            print(yaml_data)
            print(str(e)[0:100])
        output = s.getvalue()
    if output:
        return yaml_data, output


def default_yaml_sample(name, locale):
    return yaml_sample(name, None, None, locale)


def yaml_samples_for_docstring(name, fullname, docstring_data, locale=None):
    sample_objs = samples_from_docstring(fullname, docstring_data)

    output = [
        yaml_samples_for_docstring_sample(name, sample, locale)
        for sample in sample_objs
    ]
    if not output:
        output = [default_yaml_sample(name, locale)]
    return output


if __name__ == "__main__":

    out = samples_from_docstring(
        "faker.providers.BaseProvider.upc_e",
        """        together to produce the UPC-E barcode, and attempting to convert the
            barcode to UPC-A and back again to UPC-E will exhibit the behavior
            described above.

            :sample:
            :sample: base='123456'
            :sample: base='123456', number_system_digit=0
            :sample: base='123456', number_system_digit=1
            :sample: base='120000', number_system_digit=0
            :sample: base='120003', number_system_digit=0
            :sample: base='120004', number_system_digit=0
            :sample: base='120000', number_system_digit=0, safe_mode=False
            :sample: base='120003', number_system_digit=0, safe_mode=False
            :sample: base='120004', number_system_digit=0, safe_mode=False""",
    )

    print(out)
