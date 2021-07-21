# Extending Snowfakery with Python Code

## How Snowfakery Finds Plugins

The basic format is:

```yaml
- plugin: package.module.classname
```

Which is equivalent to the Python:

```python
from package.module import classname
```

If the module name and the classname are the same,
this can be shortened to:

```yaml
- plugin: package.classname
```

In that case, Snowfakery will automatically expand it to

```python
from package.classname import classname
```

Fewer keystrokes are better than more, so plugin providers are
encouraged to create plugins where the module name and
class name are the same.

Snowfakery will look for the plugin or provider in these places:

- the [Python path](https://docs.python.org/3/library/sys.html#sys.path),
- in a `plugins` directory in the same directory as the recipe,
- in a `plugins` directory below the current working directory and
- in a subdirectory of the user's home directory called `.snowfakery/plugins`.

So for example, if you had a Snowfakery file like this:

```yaml
- plugin: salesforce.org.DoGood
```

named `do_goodders/do_gooder.recipe.yml`,
you could make a file named `do_gooders/plugins/salesforce/org/DoGood.py`

And that file would contain a class like this:

```python
from snowfakery.plugins import SnowfakeryPlugin

class DoGood(SnowfakeryPlugin):
    """Plugin which does good stuff"""
    ...
```

## Writing Plugins

To write a new Plugin, make a class that inherits from `SnowfakeryPlugin` and implements either the `custom_functions()` method or a `Functions` nested class. The nested class is simple: each method represents a function to expose in the namespace. In this case the
namespace would be `DoublingPlugin` and the function name `double`:

```yaml
# examples/use_doubling_plugin.yml
- plugin: mypackage.DoublingPlugin
- object: sixer
  fields:
    six:
      DoublingPlugin.double: 3
```

```python
# examples/plugins/mypackage/DoublingPlugin.py
from snowfakery import SnowfakeryPlugin


class DoublingPlugin(SnowfakeryPlugin):
    class Functions:
        def double(self, value):
            return value * 2
```

Alternately, you can implement the `custom_functions` method.

In this case you return a Python object that implements your
methods.

```python
class Doubler:
  def double(self, value):
      return value * 2

class DoublingPlugin(SnowfakeryPlugin):
    def custom_functions(self, *args, **kwargs):
        return Doubler()
```

Make sure to accept `*args` and `**kwargs` to allow for future extensibility of the method signature.

Despite the name, plugins can also include data values rather than functions in either form of plugin. Plugins essentially use Python's `getattr` to find attributes, properties, methods or functions in the namespace of the object you return from `custom_functions()`.

### Plugin Function Return Values

Plugins can return normal Python primitive types, `datetime.date`, `ObjectRow` or `PluginResult` objects. `ObjectRow` objects represent new output records/objects. `PluginResult` objects
expose a namespace that other code can access through dot-notation. `PluginResult` instances can be
initialized with either a dict or an object that exposes the namespace through Python
`getattr()`.

If your plugin generates some special kind of data value which should be serializable
as a primitive type (usually a string), subclass `PluginResult` and add a `simplify()`
method to your subclass. That method should return a Python primitive value.

### Remebering Function Result Values

Plugins can ask Snowfakery to store their result values. In that case, they
will only be called once and the value will be used forever in a particular
context:

```python
class TimeStampPlugin(SnowfakeryPlugin):
    class Functions:
        @memorable
        def constant_time(self, _=None):
            "Return the current time and then remember it."
            return time.time()
```

Given the following YAML, there are 4 contexts and therefore 4
unique timestamps:

```yaml
# examples/plugins/test_timestamp.recipe.yml
- plugin: tests.test_custom_plugins_and_providers.TimeStampPlugin
- object: parent
  count: 2
  friends:
    - object: A
      count: 2
      fields:
        foo: ${{TimeStampPlugin.constant_time()}}
    - object: B
      count: 2
      fields:
        foo: ${{TimeStampPlugin.constant_time()}}
    - object: A
      count: 2
      fields:
        foo: ${{TimeStampPlugin.constant_time()}}
    - object: B
      count: 2
      fields:
        foo: ${{TimeStampPlugin.constant_time()}}
```

```s
$ snowfakery examples/plugins/test_timestamp.recipe.yml
parent(id=1)
A(id=1, foo=1626883921.109788)
A(id=2, foo=1626883921.109788)
B(id=1, foo=1626883921.1107168)
B(id=2, foo=1626883921.1107168)
A(id=3, foo=1626883921.111661)
A(id=4, foo=1626883921.111661)
B(id=3, foo=1626883921.1125162)
B(id=4, foo=1626883921.1125162)
parent(id=2)
A(id=5, foo=1626883921.109788)
A(id=6, foo=1626883921.109788)
B(id=5, foo=1626883921.1107168)
B(id=6, foo=1626883921.1107168)
A(id=7, foo=1626883921.111661)
A(id=8, foo=1626883921.111661)
B(id=7, foo=1626883921.1125162)
B(id=8, foo=1626883921.1125162)
```

If a function takes arguments and -- for whatever reason --
the argument values change, the memorized value will
be recomputed as if it were a new context.

```yaml
# examples/plugins/test_timestamp_args_change.recipe.yml
- plugin: tests.test_custom_plugins_and_providers.TimeStampPlugin
- object: A
  count: 5
  fields:
    blah:
      fake: Name
    foo: ${{TimeStampPlugin.constant_time(blah)}}
```

```s
$ snowfakery examples/plugins/test_timestamp_args_change.recipe.yml
A(id=1, foo=1626884493.793962)
A(id=2, foo=1626884493.794135)
A(id=3, foo=1626884493.7942772)
A(id=4, foo=1626884493.794427)
A(id=5, foo=1626884493.794549)
```

If your function accepts a special argument called "name", Snowfakery
will allow the user to reuse the value between contexts.

```yaml
# examples/plugins/test_timestamp_name_change.recipe.yml
- plugin: tests.test_custom_plugins_and_providers.TimeStampPlugin
- object: A
  fields:
    foo: ${{TimeStampPlugin.constant_time(name="first")}}
- object: A
  fields:
    foo: ${{TimeStampPlugin.constant_time(name="second")}}
- object: B
  fields:
    foo: ${{TimeStampPlugin.constant_time(name="second")}}
- object: A
  fields:
    foo: ${{TimeStampPlugin.constant_time(name="first")}}
```

```s
$ snowfakery examples/plugins/test_timestamp_name_change.recipe.yml
A(id=1, foo=1626884822.317738)
A(id=2, foo=1626884822.3186612)
B(id=1, foo=1626884822.3186612)
A(id=3, foo=1626884822.317738)
```

Memorized objects are recreated on each iteration of Snowfakery.

### Plugins with state that changes

Let's imagine we want a plugin that A) reads a file and
B) outputs a different line every time it is referred to.

The way to deal with part A is to make a `PluginResultIterator`
that represents the open file. The iterator should have a `next` method
which returns each line. This will fulfill our requirement B.

Here is the whole plugin module, including the PluginResultIterator and Plugin.

```python
# examples/plugins/OpenFiles.py
from snowfakery import SnowfakeryPlugin, PluginResultIterator, memorable
from pathlib import Path


class OpenFiles(SnowfakeryPlugin):
    class Functions:
        @memorable
        def read_line(self, filename, name=None):
            parent_directory = Path(
                str(self.context.field_vars()["snowfakery_filename"])
            ).parent
            abspath = parent_directory / filename
            return OpenFile(abspath)


class OpenFile(PluginResultIterator):

    # initialize the object's state.
    def __init__(self, filename):
        self.file = open(filename, "r")

    # cleanup later
    def close(self):
        self.file.close()

    # the main logic goes in a method called `next`
    def next(self):
        return self.file.readline().strip()
```

Here is an example YAML:

```yaml
# examples/plugins/test_open_file.yml
- plugin: examples.plugins.OpenFiles
- object: WithOpenFile
  count: 3
  fields:
    poetry_line:
      OpenFiles.read_line:
        filename: poem.txt
```

And some output:

```s
$ snowfakery examples/plugins/test_open_file.yml
WithOpenFile(id=1, poetry_line=You must never let truth get in the way of beauty,)
WithOpenFile(id=2, poetry_line=or so e.e.cummings believed.)
WithOpenFile(id=3, poetry_line="This is the wonder that's keeping the stars apart.")
```

Iterators are recreated on each iteration of Snowfakery.

As described earlier, you could open two different files using context:

```yaml
# examples/plugins/test_multiple_open_files.yml
- plugin: examples.plugins.OpenFiles
- object: parent
  count: 3
  friends:
    - object: WithOpenFile
      fields:
        poetry_line:
          OpenFiles.read_line:
            filename: poem.txt
    - object: WithOpenFile2
      fields:
        poetry_line:
          OpenFiles.read_line:
            filename: poem.txt
```

```s
$ snowfakery examples/plugins/test_multiple_open_files.yml
parent(id=1)
WithOpenFile(id=1, poetry_line=You must never let truth get in the way of beauty,)
WithOpenFile2(id=1, poetry_line=You must never let truth get in the way of beauty,)
parent(id=2)
WithOpenFile(id=2, poetry_line=or so e.e.cummings believed.)
WithOpenFile2(id=2, poetry_line=or so e.e.cummings believed.)
parent(id=3)
WithOpenFile(id=3, poetry_line="This is the wonder that's keeping the stars apart.")
WithOpenFile2(id=3, poetry_line="This is the wonder that's keeping the stars apart.")
```

And you could share a context between templates by using a `name`:

```yaml
# examples/plugins/test_shared_open_files.yml
- plugin: examples.plugins.OpenFiles
- object: parent
  friends:
    - object: WithOpenFile
      fields:
        poetry_line:
          OpenFiles.read_line:
            filename: poem.txt
            name: JohnGreenPoem
    - object: WithOpenFile2
      fields:
        poetry_line:
          OpenFiles.read_line:
            name: JohnGreenPoem
    - object: WithOpenFile3
      fields:
        poetry_line:
          OpenFiles.read_line:
            name: JohnGreenPoem
```

### Lazy evaluation

In the rare event that a plugin has a function which need its arguments to be passed to it unevaluated, for later (perhaps conditional) evaluation, you can use the `@snowfakery.lazy` decorator. Then you can evaluate the arguments with `self.context.evaluate()`.

For example:

```python
class DoubleVisionPlugin(SnowfakeryPlugin):
    class Functions:
        @lazy
        def do_it_twice(self, value):
            "Evaluates its argument twice into a string"
            rc = f"{self.context.evaluate(value)} : {self.context.evaluate(value)}"

            return rc
```

The method will evaluate its argument twice, and stick the two results into a string. For example, if it were called with a call to `random_number`, you would get two different random numbers rather than the same number twice. If it were called with the counter from above, you would get two different counter values in the string.

```yaml
  - plugin: tests.test_custom_plugins_and_providers.DoubleVisionPlugin
  - object: OBJ
    fields:
      some_value:
          - DoubleVisionPlugin.do_it_twice:
              - abc
```

This would output an `OBJ` row with values:

```python
  {'id': 1, 'some_value': 'abc : abc', 'some_value_2': '1 : 2'})
```

Occasionally you might write a plugin which needs to evaluate its
parameters lazily but doesn't care about the internals of the values
because it just returns it to some parent context. In that case,
use `context.evaluate_raw()` instead of `context.evaluate()`.

Plugins that require "memory" or "state" are possible using `PluginResult`
objects or subclasses. Consider a plugin that generates child objects
that include values that sum up values on child objects to a value specified on a parent:

```yaml
# examples/sum_child_values.yml
# This shows how you could create a plugin or feature where
# a parent object generates child objects which sum up
# to any particular value.

- plugin: examples.sum_totals.SummationPlugin
- var: summation_helper
  value:
    SummationPlugin.summer:
      total: 100
      step: 10

- object: ParentObject__c
  count: 10
  fields:
    MinimumChildObjectAmount__c: 10
    MinimumStep: 5
    TotalAmount__c: ${{summation_helper.total}}
  friends:
    - object: ChildObject__c
      count: ${{summation_helper.count}}
      fields:
        Parent__c:
          reference: ParentObject__c
        Amount__c: ${{summation_helper.next_amount}}
        RunningTotal__c: ${{summation_helper.running_total}}
```

This would generate values like this:

```json
ParentObject__c(id=1, MinimumChildObjectAmount__c=10, MinimumStep=5, TotalAmount__c=100)
ChildObject__c(id=1, Parent__c=ParentObject__c(1), Amount__c=60, RunningTotal__c=60)
ChildObject__c(id=2, Parent__c=ParentObject__c(1), Amount__c=20, RunningTotal__c=80)
ChildObject__c(id=3, Parent__c=ParentObject__c(1), Amount__c=20, RunningTotal__c=100)

ParentObject__c(id=2, MinimumChildObjectAmount__c=10, MinimumStep=5, TotalAmount__c=100)
ChildObject__c(id=4, Parent__c=ParentObject__c(2), Amount__c=40, RunningTotal__c=40)
ChildObject__c(id=5, Parent__c=ParentObject__c(2), Amount__c=20, RunningTotal__c=60)
ChildObject__c(id=6, Parent__c=ParentObject__c(2), Amount__c=40, RunningTotal__c=100)

ParentObject__c(id=3, MinimumChildObjectAmount__c=10, MinimumStep=5, TotalAmount__c=100)
ChildObject__c(id=7, Parent__c=ParentObject__c(3), Amount__c=10, RunningTotal__c=10)
ChildObject__c(id=8, Parent__c=ParentObject__c(3), Amount__c=40, RunningTotal__c=50)
ChildObject__c(id=9, Parent__c=ParentObject__c(3), Amount__c=10, RunningTotal__c=60)
ChildObject__c(id=10, Parent__c=ParentObject__c(3), Amount__c=10, RunningTotal__c=70)
ChildObject__c(id=11, Parent__c=ParentObject__c(3), Amount__c=30, RunningTotal__c=100)
```

Here is the plugin implementation:

```python
# examples/sum_totals.py
from random import randint, shuffle

from snowfakery.plugins import SnowfakeryPlugin, PluginResult


def parts(total, step):
    """Split a number into a randomized set of 'pieces'.
    The pieces add up to the number. E.g.

    parts(12, 3) -> [3, 6, 3]
    parts(16, 4) -> [8, 4, 4]

    >>> assert len(parts(12, 3)) > 1
    >>> assert sum(parts(12, 3)) == 12
    """
    assert total % step == 0
    pieces = []

    while sum(pieces) < total:
        top = (total - sum(pieces)) / step
        pieces.append(randint(1, top) * step)

    shuffle(pieces)
    return pieces


class Summation(PluginResult):
    """Represent a group of pieces"""

    def __init__(self, total, step):
        self.total = total
        self.pieces = parts(total, step)
        super().__init__(None)

    @property
    def count(self, null=None):
        return len(self.pieces)

    @property
    def next_amount(self):
        rc = self.pieces.pop()
        return rc


class SummationPlugin(SnowfakeryPlugin):
    """Plugin which generates a summataion helper"""

    class Functions:
        def summer(self, total, step):
            return Summation(total, step)
```

## Custom Providers

To write a new Provider, please refer to the [documentation for Faker](https://faker.readthedocs.io/en/master/#providers)

### Example of a custom provider

Here is an example of a simple provider:

```python
# examples/plugins/tla_provider.py
import string
import random
from faker.providers import BaseProvider


class Provider(BaseProvider):
    def ThreeLetterAcronym(self):
        alpha = string.ascii_uppercase
        letters = random.choices(alpha, k=3)
        acronym = "".join(letters)
        return acronym
```

A recipe can refer to the provider like this:

```yaml
# examples/use_custom_provider.yml
- plugin: tla_provider.Provider
- object: Company
  fields:
    technology:
      fake: ThreeLetterAcronym
```

Note the relative paths between these two files.

`examples/use_custom_provider.yml` refers to `examples/plugins/tla_provider.py` as `tla_provider.Provider` because the `plugins` folder is in the search path
described in [How Snowfakery Finds Plugins](#how-snowfakery-finds-plugins).
