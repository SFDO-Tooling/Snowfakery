# Embedding Snowfakery into Python Applications

## Simple Embedding

Snowfakery can be embedded into Python applications
by calling the `snowfakery.generate_data` function.

It can be as simple as:

```python
from snowfakery import generate_data

generate_data("filename.recipe.yaml")
```

Or:

```python
from snowfakery import generate_data

recipe = """
- object: Account
  fields:
     name:
        fake: company
"""
generate_data(StringIO(recipe))
```

The parameter is what the Snowakery API calls a
`FileLike`. `FileLike`s can be already-open
files, pathLib.Paths or string paths.

## Controlling Recipe Execution

The Snowfakery API also allows the application
to inject logic by implementing a SnowfakeryApplication
subclass:

```python
# examples/sample_app.py
from snowfakery import generate_data, SnowfakeryApplication


class MyApplication(SnowfakeryApplication):
    def __init__(self, stopping_tablename, count):
        self.count = count
        self._stopping_tablename = stopping_tablename

    def echo(self, message=None, file=None, nl=True, err=False, color=None, **kwargs):
        """Write something to a virtual stdout or stderr.

        Arguments to this function are derived from click.echo"""
        # this is a simplistic implementation! Model your real one
        # on click.echo
        if err:
            print("ERROR:" + message)
        else:
            print(message)

    @property
    def stopping_tablename(self, **kwargs):
        """Return the name of "stopping table/object":

        The table/object whose presence determines
        whether we are done generating data.

        This is used by Snowfakery to validate that
        the provided recipe will not generate forever
        due to a misspelling the stopping tablename."""
        return self._stopping_tablename

    def check_if_finished(self, id_manager, **kwargs):
        """Check if we're finished generating"""
        print("Checking if finished:", id_manager[self.stopping_tablename])
        return id_manager[self.stopping_tablename] >= self.count


myapp = MyApplication("Employee", 100)
generate_data("examples/company.yml", parent_application=myapp, output_file="out.json")
```

The only thing you can do with the `id_manager` is look up the highest
integer `id` which has been assigned to a particular tablename (presumably
the `stopping_tablename`).

As you can see above, the two main extensbility points are
a) where warning/logging output goes and b) controlling
when to finish looping over a recipe.

Always accept `**kwargs` as arguments to allow new arguments to
be added by Snowfakery over time.

## All arguments to generate_data

The complete method declaration for `generate_data` is as follows:

```python
def generate_data(
    yaml_file: FileLike,
    *,
    parent_application: SnowfakeryApplication = None,  # the parent application
    user_options: T.Dict[str, str] = None,  # same as --option
    dburl: str = None,  # same as --dburl
    dburls=[],  # same as multiple --dburl options
    target_number: T.Tuple = None,  # same as --target-number
    debug_internals: bool = None,  # same as --debug-internals
    generate_cci_mapping_file: FileLike = None,  # same as --generate-cci-mapping-file
    output_format: str = None,  # same as --output-format
    output_file: FileLike = None,  # same as --output-file
    output_files: T.List[FileLike] = None,  # same as multiple --output-file options
    output_folder: FileLike = None,  # same as --output-folder
    continuation_file: FileLike = None,  # continuation file from last execution
    generate_continuation_file: FileLike = None,  # place to generate continuation file
    should_create_cci_record_type_tables: bool = False,  # create CCI Record type tables?
    load_declarations: T.Sequence[FileLike] = None,  # read these load declarations for CCI 
    plugin_options:Mapping = None,
) -> None:
```
