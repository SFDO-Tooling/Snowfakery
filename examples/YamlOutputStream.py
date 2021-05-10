import yaml

from snowfakery.output_streams import FileOutputStream


class YamlOutputStream(FileOutputStream):
    is_text = True

    def __init__(self, filename, **kwargs):
        super().__init__(filename, **kwargs)
        self.out = []

    def write_single_row(self, tablename: str, row: dict) -> None:
        self.out.append(
            {"object": tablename, "nickname": f"row_{row['id']}", "fields": row}
        )

    def flatten(
        self,
        sourcetable: str,
        fieldname: str,
        source_row_dict: dict,
        target_object_row,
    ):
        return {"reference": f"row_{target_object_row.id}"}

    def close(self):
        yaml.dump(self.out, self.stream, sort_keys=False)
