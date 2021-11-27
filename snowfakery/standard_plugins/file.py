from snowfakery.plugins import SnowfakeryPlugin
from pathlib import Path


class File(SnowfakeryPlugin):
    class Functions:
        def file_data(self, file, encoding="utf-8"):
            if encoding == "binary":
                encoding = "latin-1"

            template_path = Path(self.context.current_filename).parent

            with open(template_path / file, "rb") as data:
                return data.read().decode(encoding)
