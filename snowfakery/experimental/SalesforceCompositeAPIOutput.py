# Use this experimental OutputStream like this:

# snowfakery --output-format snowfakery.experimental.SalesforceCompositeAPIOutput recipe.yml > composite.json
#
# Once you have the file you can make it accessible to Salesforce by uploading it
# to some form of server. E.g. Github gist, Heroku, etc.
#
# Then you can use Anon Apex like that in `LoadCompositeAPIData.apex` to load it into
# any org. e.g.:

# sfdx force:apex:execute -f ./examples/salesforce/LoadCompositeAPIData.apex -u Snowfakery__qa
# or
# cci task run execute_anon --path examples/salesforce/LoadCompositeAPIData.apex --org qa
#
# Note that Salesforce will complain if the dataset has more than 500 rows.

# TODO: Add tests

import json
import typing as T
import datetime
from pathlib import Path
from tempfile import TemporaryDirectory

from snowfakery.output_streams import FileOutputStream, OutputStream

MAX_BATCH_SIZE = 500  # https://developer.salesforce.com/docs/atlas.en-us.api_rest.meta/api_rest/resources_composite_graph_limits.htm


class SalesforceCompositeAPIOutput(FileOutputStream):
    """Output stream that generates records for Salesforce's Composite API"""

    encoders: T.Mapping[type, T.Callable] = {
        **FileOutputStream.encoders,
        datetime.date: str,
        datetime.datetime: str,
        bool: bool,
    }
    is_text = True

    def __init__(self, file, **kwargs):
        assert file
        super().__init__(file, **kwargs)
        self.rows = []

    def write_single_row(self, tablename: str, row: T.Dict) -> None:
        row_without_id = row.copy()
        del row_without_id["id"]
        values = {
            "method": "POST",
            "referenceId": f"{tablename}_{row['id']}",
            "url": f"/services/data/v50.0/sobjects/{tablename}",
            "body": row_without_id,
        }
        self.rows.append(values)

    def flatten(
        self,
        sourcetable: str,
        fieldname: str,
        source_row_dict,
        target_object_row,
    ) -> T.Union[str, int]:
        target_reference = f"{target_object_row._tablename}_{target_object_row.id}"
        return "@{%s.id}" % target_reference

    def close(self, **kwargs) -> T.Optional[T.Sequence[str]]:
        # NOTE: Could improve loading performance by breaking graphs up
        # to allow server-side parallelization, but I'd risk locking issues
        data = {"graphs": [{"graphId": "graph", "compositeRequest": self.rows}]}
        self.write(json.dumps(data, indent=2))
        return super().close()


class Folder(OutputStream):
    uses_folder = True

    def __init__(self, output_folder, **kwargs):
        super().__init__(None, **kwargs)
        self.target_path = Path(output_folder)
        if not Path.exists(self.target_path):
            Path.mkdir(self.target_path, exist_ok=True)  # pragma: no cover
        self.recipe_sets = [[]]
        self.current_batch = []
        self.filenum = 0
        self.filenames = []

    def write_row(self, tablename: str, row_with_references: T.Dict) -> None:
        self.recipe_sets[-1].append((tablename, row_with_references))

    def write_single_row(self, tablename: str, row: T.Dict) -> None:
        raise NotImplementedError(
            "Shouldn't be called. write_row should be called instead"
        )

    def close(self, **kwargs) -> T.Optional[T.Sequence[str]]:
        self.flush_sets()
        self.flush_batch()
        table_metadata = [{"url": str(filename)} for filename in self.filenames]
        metadata = {
            "@context": "http://www.w3.org/ns/csvw",
            "tables": table_metadata,
        }
        metadata_filename = self.target_path / "csvw_metadata.json"
        with open(metadata_filename, "w") as f:
            json.dump(metadata, f, indent=2)
        return [f"Created {self.target_path}"]

    def complete_recipe(self, *args):
        self.flush_sets()
        self.recipe_sets.append([])

    def flush_sets(self):
        while self.recipe_sets:
            next_set = self.recipe_sets.pop(0)
            if len(self.current_batch) + len(next_set) > MAX_BATCH_SIZE:
                self.flush_batch()
            self.current_batch.extend(next_set)

    def flush_batch(self):
        self.filenum += 1
        filename = Path(self.target_path) / f"{self.filenum}.composite.json"

        with open(filename, "w") as open_file, SalesforceCompositeAPIOutput(
            open_file
        ) as out:
            self.filenames.append(filename)
            print(len(self.current_batch))
            for tablename, row in self.current_batch:
                out.write_row(tablename, row)

        self.current_batch = []


class Bundle(FileOutputStream):
    def __init__(self, file, **kwargs):
        super().__init__(file, **kwargs)
        self.tempdir = TemporaryDirectory()
        self.folder_os = Folder(self.tempdir.name)

    def write_row(self, tablename: str, row_with_references: T.Dict) -> None:
        self.folder_os.write_row(tablename, row_with_references)

    def write_single_row(self, tablename: str, row: T.Dict) -> None:
        raise NotImplementedError(
            "Shouldn't be called. write_row should be called instead"
        )

    def complete_recipe(self, *args):
        self.folder_os.complete_recipe()

    def close(self):
        self.folder_os.close()
        data = self.organize_bundle()
        self.write(json.dumps(data, indent=2))
        self.tempdir.cleanup()
        return super().close()

    def organize_bundle(self):
        files = Path(self.tempdir.name).glob("*.composite.json")
        data = [file.read_text() for file in files]
        assert data
        return {"bundle_format": 1, "data": data}
