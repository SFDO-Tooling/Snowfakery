from snowfakery import generate_data
from io import StringIO
from timeit import timeit

yaml = "- object: Foo"


def gen():
    with StringIO(yaml) as f:
        generate_data(f, output_file="/dev/null", output_format="txt")


print(timeit(gen, number=1))
