# Use this experimental OutputStream like this:

# snowfakery --output-format snowfakery.experimental.SalesforceCompositeOutput recipe.yml > composite.json
#
# Once you have the file you can make it accessible to Salesforce by uploading it
# to some form of server. E.g. Github gist, Heroku, etc.
#
# Then you can use Anon Apex like that in `ReadCompositeAPIData.apex` to load it into
# any org.

import json
import typing as T
import datetime

from snowfakery.output_streams import FileOutputStream


class SalesforceCompositeOutput(FileOutputStream):
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
