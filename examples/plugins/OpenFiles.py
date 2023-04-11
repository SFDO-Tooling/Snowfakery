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
