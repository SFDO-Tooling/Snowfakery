from snowfakery.plugins import SnowfakeryPlugin
from pathlib import Path


class File(SnowfakeryPlugin):
    class Functions:
        def file_data(self, file, encoding="utf-8"):
            if encoding == "binary":
                encoding = "latin-1"

            context_filename = Path(
                self.context.interpreter.current_context.current_template.filename
            ).parent

            with open(context_filename / file, "rb") as data:
                return data.read().decode(encoding)
