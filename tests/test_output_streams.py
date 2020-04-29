import unittest
from abc import ABC, abstractmethod
from io import StringIO
import json
import datetime
import csv
from pathlib import Path
from tempfile import TemporaryDirectory
from contextlib import redirect_stdout
from tests.utils import named_temporary_file_path

from sqlalchemy import create_engine

from snowfakery.output_streams import (
    SqlOutputStream,
    JSONOutputStream,
    CSVOutputStream,
)

from snowfakery.data_generator import generate
from snowfakery.cli import generate_cli


sample_yaml = Path(__file__).parent / "include_parent.yml"


def normalize(row):
    return {f: str(row[f]) for f in row if row[f] is not None and row[f] != ""}


class OutputCommonTests(ABC):
    @abstractmethod
    def do_output(self, yaml):
        raise NotImplementedError

    def test_dates(self):
        yaml = """
        - object: foo
          fields:
            y2k: <<date(year=2000, month=1, day=1)>>
            party: <<datetime(year=1999, month=12, day=31, hour=23, minute=59, second=59)>>
            randodate:
                date_between:
                    start_date: 2000-02-02
                    end_date: 2010-01-01
        """
        tables = self.do_output(yaml)
        values = tables["foo"][0]
        assert values["y2k"] == str(datetime.date(year=2000, month=1, day=1))
        assert values["party"] == str(
            datetime.datetime(
                year=1999, month=12, day=31, hour=23, minute=59, second=59
            )
        )
        assert len(values["randodate"].split("-")) == 3
        assert values["randodate"].startswith("200")

    def test_bool(self):
        yaml = """
        - object: foo
          fields:
            is_true: True
            """
        values = self.do_output(yaml)["foo"][0]
        assert str(values["is_true"]) == "1"

    def test_null(self):
        yaml = """
        - object: foo
          fields:
            is_null:
            """
        values = self.do_output(yaml)["foo"][0]
        print(values)
        assert values["is_null"] is None

    def test_flushes(self):
        yaml = """
        - object: foo
          count: 15
          fields:
            a: b
            c: 3
        - object: bar
          count: 1
        """

        class MockFlush:
            def __init__(self, real_flush):
                self.real_flush = real_flush
                self.flush_count = 0

            def __call__(self):
                self.flush_count += 1
                self.real_flush()

        results = self.do_output(yaml)
        assert len(list(results["foo"])) == 15
        assert len(list(results["bar"])) == 1

    def test_inferred_schema(self):
        yaml = """
        - object: foo
          fields:
            a: 1
            c: 3
        - object: foo
          fields:
            b: 2
            d: 4
        """
        result = self.do_output(yaml)["foo"]
        assert tuple(normalize(dict(row)) for row in result) == (
            normalize({"id": "1", "a": "1", "c": "3"}),
            normalize({"id": "2", "b": "2", "d": "4"}),
        )

    def test_suppressed_values(self):
        yaml = """
        - object: foo
          fields:
            __a: 1
            c: 3
        - object: foo
          fields:
            b: 2
            __d: 4
        """
        result = self.do_output(yaml)["foo"]
        assert tuple(normalize(dict(row)) for row in result) == (
            normalize({"id": "1", "c": "3"}),
            normalize({"id": "2", "b": "2"}),
        )


class TestSqlOutputStream(unittest.TestCase, OutputCommonTests):
    def do_output(self, yaml):
        with named_temporary_file_path() as f:
            url = f"sqlite:///{f}"
            output_stream = SqlOutputStream.from_url(url, None)
            results = generate(StringIO(yaml), {}, output_stream)
            table_names = results.tables.keys()
            output_stream.close()
            engine = create_engine(url)
            with engine.connect() as connection:
                tables = {
                    table_name: list(connection.execute(f"select * from {table_name}"))
                    for table_name in table_names
                }
                return tables

    def test_null(self):
        yaml = """
        - object: foo
          fields:
            is_null:
            """
        values = self.do_output(yaml)["foo"][0]
        assert values["is_null"] is None


class JSONTables:
    def __init__(self, json_data, table_names):
        self.raw = json_data
        self.data = json.loads(json_data)
        self.tables = {table_name: [] for table_name in table_names}
        for row in self.data:
            r = row.copy()
            tablename = r.pop("_table")
            self.tables[tablename].append(r)

    def __getitem__(self, name):
        return self.tables[name]


class TestJSONOutputStream(unittest.TestCase, OutputCommonTests):
    def do_output(self, yaml):
        with StringIO() as s:
            output_stream = JSONOutputStream(s)
            results = generate(StringIO(yaml), {}, output_stream)
            output_stream.close()
            return JSONTables(s.getvalue(), results.tables.keys())

    def test_json_output_real(self):
        yaml = """
        - object: foo
          count: 15
          fields:
            a: b
            c: 3
        """

        output_stream = JSONOutputStream(StringIO())
        generate(StringIO(yaml), {}, output_stream)
        output_stream.close()

    def test_json_output_mocked(self):
        yaml = """
        - object: foo
          count: 2
          fields:
            a: b
            c: 3
        """

        stdout = StringIO()
        output_stream = JSONOutputStream(stdout)
        generate(StringIO(yaml), {}, output_stream)
        output_stream.close()
        assert json.loads(stdout.getvalue()) == [
            {"_table": "foo", "a": "b", "c": 3.0, "id": 1},
            {"_table": "foo", "a": "b", "c": 3.0, "id": 2},
        ]

    def test_from_cli(self):
        x = StringIO()
        with redirect_stdout(x):
            generate_cli.callback(
                yaml_file=sample_yaml, output_format="json",
            )
        data = json.loads(x.getvalue())
        assert data == [
            {
                "_table": "Account",
                "id": 1,
                "name": "Default Company Name",
                "ShippingCountry": "Canada",
            }
        ]

    def test_null(self):
        yaml = """
        - object: foo
          fields:
            is_null:
            """
        output = self.do_output(yaml)
        assert "null" in output.raw
        values = output["foo"][0]
        assert values["is_null"] is None


class TestCSVOutputStream(unittest.TestCase, OutputCommonTests):
    def do_output(self, yaml):
        with TemporaryDirectory() as t:
            output_stream = CSVOutputStream(Path(t) / "csvoutput")
            results = generate(StringIO(yaml), {}, output_stream)
            output_stream.close()
            table_names = results.tables.keys()
            tables = {}
            for table in table_names:
                pathname = Path(t) / "csvoutput" / (table + ".csv")
                assert pathname.exists()
                with open(pathname) as f:
                    tables[table] = list(csv.DictReader(f))
            return tables

    def test_csv_output(self):
        yaml = """
        - object: foo
          fields:
            a: 1
            c: 3
        - object: foo
          fields:
            b: 2
            d: 4
        - object: bar
          fields:
            barb: 2
            bard: 4
        """
        with TemporaryDirectory() as t:
            output_stream = CSVOutputStream(Path(t) / "csvoutput")
            generate(StringIO(yaml), {}, output_stream)
            messages = output_stream.close()
            assert "foo.csv" in messages[0]
            assert "bar.csv" in messages[1]
            assert "csvw" in messages[2]
            assert (Path(t) / "csvoutput" / "foo.csv").exists()
            with open(Path(t) / "csvoutput" / "csvw_metadata.json") as f:
                metadata = json.load(f)
                assert {table["url"] for table in metadata["tables"]} == {
                    "foo.csv",
                    "bar.csv",
                }

    def test_null(self):
        yaml = """
        - object: foo
          fields:
            is_null:
            """
        values = self.do_output(yaml)["foo"][0]
        print(values)
        assert (
            values["is_null"] == ""
        )  # CSV is no way of distingushing null from empty str
