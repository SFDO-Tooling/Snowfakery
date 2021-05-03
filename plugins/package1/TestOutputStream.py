from snowfakery.output_streams import FileOutputStream


class TestOutputStream(FileOutputStream):
    is_text = True

    def write_single_row(self, tablename: str, row: dict) -> None:
        self.write(f"{tablename} - {repr(row)}\n")

    def flatten(
        self,
        sourcetable: str,
        fieldname: str,
        source_row_dict: dict,
        target_object_row,
    ):
        return f"{target_object_row._tablename}({target_object_row.id})"
