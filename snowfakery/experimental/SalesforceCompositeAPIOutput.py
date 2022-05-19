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

from snowfakery.output_streams import FileOutputStream, OutputStream


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
        data = {"graphs": [{"graphId": "graph", "compositeRequest": self.rows}]}
        self.write(json.dumps(data, indent=2))
        return super().close()


class Folder(OutputStream):
    uses_folder = True

    def __init__(self, output_folder, **kwargs):
        super().__init__(None, **kwargs)
        self.target_path = Path(output_folder)
        if not Path.exists(self.target_path):
            Path.mkdir(self.target_path, exist_ok=True)
        self.recipe_sets = [[]]
        self.filenum = 0
        self.filenames = []

    def write_single_row(self, tablename: str, row: T.Dict) -> None:
        self.recipe_sets[-1].append((tablename, row))

    def close(self, **kwargs) -> T.Optional[T.Sequence[str]]:
        self.flush_sets()
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
        ready_rows = sum(len(s) for s in self.recipe_sets)
        if ready_rows > 500:
            self.flush_sets()
        self.recipe_sets.append([])

    def flush_sets(self):
        sets = self.recipe_sets
        batches = [[]]
        for set in sets:
            if len(batches[-1]) + len(set) > 500:
                batches.append(set.copy())
            else:
                batches[-1].extend(set)
        for batch in batches:
            if len(batch):
                self.filenum += 1
                filename = Path(self.target_path) / f"{self.filenum}.composite.json"
                self.save_batch(filename, batch)

    def save_batch(self, filename, batch):
        with open(filename, "w") as open_file, SalesforceCompositeAPIOutput(
            open_file
        ) as out:
            self.filenames.append(filename)
            for tablename, row in batch:
                out.write_row(tablename, row)
