from abc import abstractmethod, ABC
import json
from tempfile import TemporaryDirectory
import csv
import subprocess
import datetime
import sys
from pathlib import Path
from collections import namedtuple, defaultdict
from typing import Dict, Union, Optional, Mapping, Callable, Sequence
from warnings import warn

from sqlalchemy import (
    create_engine,
    MetaData,
    Column,
    Integer,
    Table,
    Unicode,
    func,
    inspect,
)
from sqlalchemy.ext.automap import automap_base
from sqlalchemy.orm import create_session
from sqlalchemy.engine import Engine
from sqlalchemy.sql import select

from .data_gen_exceptions import DataGenError

from .object_rows import ObjectRow, ObjectReference
from .parse_recipe_yaml import TableInfo


def noop(x):
    return x


class OutputStream(ABC):
    """Common base class for all output streams"""

    count = 1
    flush_limit = 1000
    commit_limit = 10000
    encoders: Mapping[type, Callable] = {
        str: str,
        int: int,
        float: float,
        datetime.date: noop,
        datetime.datetime: noop,
        type(None): noop,
        bool: int,
    }
    uses_folder = False
    uses_path = False
    is_text = False

    def __init__(self, filename, **kwargs):
        pass

    def create_or_validate_tables(self, tables: Dict[str, TableInfo]) -> None:
        pass

    def flatten(
        self,
        sourcetable: str,
        fieldname: str,
        source_row_dict: Dict,
        target_object_row: Union[ObjectRow, ObjectReference],
    ) -> Union[str, int]:
        return target_object_row.id

    def flush(self):
        pass

    def commit(self):
        pass

    def cleanup(self, field_name, field_value, sourcetable, row):
        if isinstance(field_value, (ObjectRow, ObjectReference)):
            return self.flatten(sourcetable, field_name, row, field_value)
        else:
            encoder = self.encoders.get(type(field_value))
            if not encoder and hasattr(field_value, "simplify"):

                def encoder(field_value):
                    return field_value.simplify()

            if not encoder:
                raise TypeError(
                    f"No encoder found for {type(field_value)} in {self.__class__.__name__} "
                    f"for {field_name}, {field_value} in {sourcetable}"
                )
            return encoder(field_value)

    def should_output(self, value):
        return not value.startswith("__")

    def write_row(self, tablename: str, row_with_references: Dict) -> None:
        should_output = self.should_output
        row_cleaned_up_and_flattened = {
            field_name: self.cleanup(
                field_name, field_value, tablename, row_with_references
            )
            for field_name, field_value in row_with_references.items()
            if should_output(field_name)
        }
        self.write_single_row(tablename, row_cleaned_up_and_flattened)
        if self.count % self.flush_limit == 0:
            self.flush()

        if self.count % self.commit_limit == 0:
            self.commit()

        self.count += 1

    @abstractmethod
    def write_single_row(self, tablename: str, row: Dict) -> None:
        """Write a single row to the stream"""
        pass

    def close(self) -> Optional[Sequence[str]]:
        """Close any resources the stream opened.

        Do not close file handles which were passed in!

        Return a list of messages to print out.
        """
        return super().close()

    def __enter__(self, *args):
        return self

    def __exit__(self, *args):
        self.close()


class SmartStream:
    """Common code for managing stream/file opening/closing

    Expects to be initialized with either a file-like object with a `write` method,
    or a path (str or pathlib.Path) that can be opened using `open()`
    """

    mode = "wt"

    def __init__(self, stream_or_path=None):
        if hasattr(stream_or_path, "write"):
            self.owns_stream = False
            self.stream = stream_or_path
        elif stream_or_path:
            self.stream = open(stream_or_path, self.mode)
            self.owns_stream = True
        elif stream_or_path is None:
            self.owns_stream = False
            self.stream = sys.stdout
        else:  # noqa
            assert False, f"stream_or_path is {stream_or_path}"

    def write(self, data):
        self.stream.write(data)

    def close(self):
        if self.owns_stream:
            self.stream.close()
            return [f"Generated {self.stream.name}"]


class FileOutputStream(OutputStream):
    """Base class for all file/stream-based OutputStreams"""

    def __init__(self, stream_or_path=None, **kwargs):
        self.smart_stream = SmartStream(stream_or_path)
        self.write = self.smart_stream.write
        self.stream = self.smart_stream.stream

    def close(self):
        return self.smart_stream.close()


class DebugOutputStream(FileOutputStream):
    """Simplified output for debugging Snowfakery files."""

    is_text = True

    def write_single_row(self, tablename: str, row: Dict) -> None:
        values = ", ".join([f"{key}={value}" for key, value in row.items()])
        self.write(f"{tablename}({values})\n")

    def flatten(
        self,
        sourcetable: str,
        fieldname: str,
        source_row_dict: Dict,
        target_object_row: Union[ObjectRow, ObjectReference],
    ) -> Union[str, int]:
        return f"{target_object_row._tablename}({target_object_row.id})"


CSVContext = namedtuple("CSVContext", ["dictwriter", "file"])


class CSVOutputStream(OutputStream):
    """Output stream that generates a directory of CSV files."""

    uses_folder = True

    def __init__(self, output_folder, **kwargs):
        super().__init__(None, **kwargs)
        self.target_path = Path(output_folder)
        if not Path.exists(self.target_path):
            Path.mkdir(self.target_path, exist_ok=True)

    def open_writer(self, table_name, table):
        file = open(self.target_path / f"{table_name}.csv", "w")
        writer = csv.DictWriter(file, list(table.fields.keys()) + ["id"])
        writer.writeheader()
        return CSVContext(dictwriter=writer, file=file)

    def create_or_validate_tables(self, tables: Dict[str, TableInfo]) -> None:
        self.writers = {
            table_name: self.open_writer(table_name, table)
            for table_name, table in tables.items()
        }

    def write_single_row(self, tablename: str, row: Dict) -> None:
        self.writers[tablename].dictwriter.writerow(row)

    def close(self) -> Optional[Sequence[str]]:
        messages = []
        for context in self.writers.values():
            context.file.close()
            messages.append(f"Created {context.file.name}")

        table_metadata = [
            {"url": f"{table_name}.csv"} for table_name, writer in self.writers.items()
        ]
        csv_metadata = {
            "@context": "http://www.w3.org/ns/csvw",
            "tables": table_metadata,
        }
        csvw_filename = self.target_path / "csvw_metadata.json"
        with open(csvw_filename, "w") as f:
            json.dump(csv_metadata, f, indent=2)
        messages.append(f"Created {csvw_filename}")
        return messages


class JSONOutputStream(FileOutputStream):
    encoders: Mapping[type, Callable] = {
        **OutputStream.encoders,
        datetime.date: str,
        datetime.datetime: str,
    }
    is_text = True

    def __init__(self, file, **kwargs):
        assert file
        super().__init__(file, **kwargs)
        self.first_row = True

    def write_single_row(self, tablename: str, row: Dict) -> None:
        if self.first_row:
            self.write("[")
            self.first_row = False
        else:
            self.write(",\n")
        values = {"_table": tablename, **row}
        self.write(json.dumps(values))

    def close(self) -> Optional[Sequence[str]]:
        if not self.first_row:
            self.write("]\n")
        return super().close()


class SqlDbOutputStream(OutputStream):
    """Output stream for talking to SQL Databases"""

    should_close_session = False

    def __init__(self, engine: Engine, mappings: None = None, **kwargs):
        if mappings:
            warn("Please do not pass mappings argument to __init__", DeprecationWarning)
        self.buffered_rows = defaultdict(list)
        self.table_info = {}
        self.engine = engine
        self.session = create_session(bind=self.engine, autocommit=False)
        self.metadata = MetaData(bind=self.engine)
        self.base = automap_base(bind=engine, metadata=self.metadata)

    @classmethod
    def from_url(cls, db_url: str, mappings: None = None):
        if mappings:
            warn("Please do not pass mappings argument to from_url", DeprecationWarning)
        engine = create_engine(db_url)
        self = cls(engine)
        return self

    def write_single_row(self, tablename: str, row: Dict) -> None:
        # cache the value for later insert
        self.buffered_rows[tablename].append(row)

    def flush(self):
        for tablename, (insert_statement, fallback_dict) in self.table_info.items():

            # Make sure every row has the same records per SQLAlchemy's rules

            # According to the SQL Alchemy docs, every dictionary in a set must
            # have the same keys.

            # This means that the INSERT statement will be more bloated but it
            # seems much more efficient than line-by-line inserts.
            values = [
                {
                    key: row[key] if key in row else fallback_dict[key]
                    for key in fallback_dict.keys()
                }
                for row in self.buffered_rows[tablename]
            ]
            if values:
                self.session.execute(insert_statement, values)
            self.buffered_rows[tablename] = []
        self.session.flush()

    def commit(self):
        self.flush()
        self.session.commit()

    def close(self) -> Optional[Sequence[str]]:
        self.commit()
        self.session.close()

    def create_or_validate_tables(self, inferred_tables: Dict[str, TableInfo]) -> None:
        create_tables_from_inferred_fields(inferred_tables, self.engine, self.metadata)
        self.metadata.create_all()
        self.base.prepare(self.engine, reflect=True)

        # Setup table info used by the write-buffering infrastructure
        TableTuple = namedtuple("TableTuple", ["insert_statement", "fallback_dict"])

        for tablename, model in self.metadata.tables.items():
            if tablename in inferred_tables:
                self.table_info[tablename] = TableTuple(
                    insert_statement=model.insert(bind=self.engine, inline=True),
                    fallback_dict={
                        key: None for key in inferred_tables[tablename].fields.keys()
                    },
                )
                # id is special
                self.table_info[tablename].fallback_dict.setdefault("id", None)


# backwards-compatible name for CCI
SqlOutputStream = SqlDbOutputStream


class SqlTextOutputStream(FileOutputStream):
    """Output stream to generate a SQL text file"""

    mode = "wt"
    is_text = True

    def __init__(self, stream_or_path=None, **kwargs):
        self.text_output = SmartStream(stream_or_path)
        self.tempdir = TemporaryDirectory()
        self.sql_db = self._init_db()
        super().__init__(**kwargs)

    def _init_db(self):
        "Initialize a db through an owned output stream"
        db_url = f"sqlite:///{self.tempdir.name}/tempdb.db"
        engine = create_engine(db_url)
        return SqlDbOutputStream(engine)

    def write_single_row(self, tablename: str, row: Dict) -> None:
        self.sql_db.write_single_row(tablename, row)
        # it might seem logical to try and output the raw SQL here
        # but it gets messy due to limitations of SQL Alchemy
        # https://docs.sqlalchemy.org/en/13/faq/sqlexpressions.html#rendering-bound-parameters-inline
        # in particular datetime values do not render properly without extra code
        # perhaps there are other, similar, undiscovered limitations.

    def create_or_validate_tables(self, tables: Dict[str, TableInfo]) -> None:
        self.sql_db.create_or_validate_tables(tables)

    def flush(self):
        self.sql_db.flush()

    def _dump_db(self):
        "Dump a database as a sql file"
        self.sql_db.commit()
        con = self.sql_db.engine.raw_connection()

        # https://docs.python.org/3/library/sqlite3.html#sqlite3.Connection.iterdump
        for line in con.iterdump():
            self.text_output.stream.write("%s\n" % line)

    def close(self, *args, **kwargs):
        self._dump_db()
        self.sql_db.close(*args, **kwargs)
        self.text_output.close(*args, **kwargs)
        self.tempdir.cleanup()


def create_tables_from_inferred_fields(tables, engine, metadata):
    """Create tables based on dictionary of tables->field-list."""
    with engine.connect() as conn:
        inspector = inspect(engine)
        for table_name, table in tables.items():
            columns = [Column(field_name, Unicode(255)) for field_name in table.fields]
            id_column_as_list = [
                column for column in columns if column.name.lower() == "id"
            ]

            # this code primarily supports using this function for
            # the SOQLDataSet and other datasets where ID may already exists
            if id_column_as_list:
                id_column = id_column_as_list[0]
            else:
                id_column = Column(
                    "id", Integer(), primary_key=True, autoincrement=True
                )

            t = Table(table_name, metadata, id_column, *columns)

            if inspector.has_table(table_name):
                stmt = select([func.count(t.c.id)])
                count = conn.execute(stmt).first()[0]
                if count > 0:
                    raise DataGenError(
                        f"Table already exists and has data: {table_name} in {engine.url}",
                    )


def find_name_in_dict(d):
    "Try to find a key that is semantically a 'name' for diagramming purposes."
    keys = {k.lower().replace("_", ""): k for k in d.keys()}
    if "name" in keys:
        return d[keys["name"]]
    elif "firstname" in keys or "lastname" in keys:
        firstname = d[keys.get("firstname")] if keys.get("firstname") else ""
        lastname = d[keys.get("lastname")] if keys.get("lastname") else ""
        return " ".join([firstname, lastname])
    elif "name" in str(" ".join(d.keys())):
        namekey = [k for k in d.keys() if "name" in k][0]
        return d[namekey]
    elif "id" in keys:
        return d[keys["id"]]


class GraphvizOutputStream(FileOutputStream):
    """Generates a Graphviz .dot file"""

    is_text = True

    def __init__(self, path, **kwargs):
        import gvgen

        super().__init__(path, **kwargs)

        self.nodes = {}
        self.links = []
        self.G = gvgen.GvGen()
        self.G.styleDefaultAppend("fontsize", "10")
        self.G.styleDefaultAppend("style", "filled")
        self.G.styleDefaultAppend("fillcolor", "#009EDB")
        self.G.styleDefaultAppend("fontcolor", "#FFFFFF")
        self.G.styleDefaultAppend("height", "0.75")
        self.G.styleDefaultAppend("width", "0.75")
        self.G.styleDefaultAppend("widshapeth", "circle")

    def flatten(
        self,
        sourcetable: str,
        fieldname: str,
        source_row_dict: Dict,
        target_object_row: Union[ObjectRow, ObjectReference],
    ) -> Union[str, int]:
        source = (sourcetable, source_row_dict["id"])
        target = (target_object_row._tablename, target_object_row.id)
        self.links.append((fieldname, source, target))
        return ""

    def generate_node_name(
        self, tablename: str, rowname, id: Optional[int] = None
    ) -> str:
        rowname = (", " + rowname) if rowname and rowname != id else ""
        return f"{tablename}({id}{rowname})"

    def write_single_row(self, tablename: str, row: Dict) -> None:
        node_name = self.generate_node_name(
            tablename, find_name_in_dict(row), row["id"]
        )
        self.nodes[tablename, row["id"]] = self.G.newItem(node_name)

    def close(self) -> Optional[Sequence[str]]:
        for fieldname, source, target in self.links:
            mylink = self.G.newLink(self.nodes[source], self.nodes[target])
            self.G.propertyAppend(mylink, "label", fieldname)
        self.G.dot(self.stream)
        return super().close()


DOT_MISSING_MESSAGE = """
Could not find `dot` executable.

Please install graphviz and ensure that the command `dot` is available.
For example, on Mac you could try `brew install graphviz`
On Windows you could try `winget install graphviz` or `choco install graphviz`
Other installation options are here: http://www.graphviz.org/download/

If you have installed graphviz but Snowfakery cannot find it, perhaps you
will need to use Snowfakery to generate a dotfile (--output-file=out.dot)
and then you can convert it to another format yourself as described here:
https://stackoverflow.com/a/1494495/113477

If your data is not private, you could even use one of the online
converters that you can find by searching the Web for
"convert dot file to png online".
"""


class ImageOutputStream(OutputStream):
    """Output an Image file in a graphviz supported format."""

    mode = "wb"
    uses_path = True

    def __init__(self, path, format, **kwargs):
        self.path = path
        self.format = format
        self.tempdir = TemporaryDirectory()
        self.dotfile = Path(self.tempdir.name) / "temp.dot"
        self.gv_os = GraphvizOutputStream(self.dotfile)

    def write_single_row(self, *args, **kwargs):
        return self.gv_os.write_single_row(*args, **kwargs)

    def flatten(self, *args, **kwargs):
        return self.gv_os.flatten(*args, **kwargs)

    def close(self) -> Optional[Sequence[str]]:
        self.gv_os.close()
        assert self.dotfile.exists()
        rc = self._render(self.dotfile, self.path)
        self.tempdir.cleanup()
        return rc or [f"Generated {self.path}"]

    def _render(self, dotfile, outfile):
        assert dotfile.exists()
        try:
            out = subprocess.Popen(
                ["dot", "-T" + self.format, dotfile, "-o" + str(outfile)],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
            )
            stdout, stderr = out.communicate()
            stdout = [stdout.decode("ASCII")] if stdout else []
            stderr = [stderr.decode("ASCII")] if stderr else []
        except FileNotFoundError:
            return [DOT_MISSING_MESSAGE]
        return stdout + stderr


class MultiplexOutputStream(OutputStream):
    """Generate multiple output streams at once."""

    def __init__(self, outputstreams, **kwargs):
        self.outputstreams = outputstreams
        super().__init__(None, **kwargs)

    def create_or_validate_tables(self, tables: Dict[str, TableInfo]) -> None:
        for stream in self.outputstreams:
            stream.create_or_validate_tables(tables)

    def write_row(self, tablename: str, row_with_references: Dict) -> None:
        for stream in self.outputstreams:
            stream.write_row(tablename, row_with_references)

    def close(self) -> Optional[Sequence[str]]:
        for stream in self.outputstreams:
            stream.close()

    def write_single_row(self, tablename: str, row: Dict) -> None:
        return super().write_single_row(tablename, row)
