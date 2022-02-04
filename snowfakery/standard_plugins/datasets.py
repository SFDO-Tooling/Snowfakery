import os
from contextlib import contextmanager, ExitStack
from csv import DictReader
from pathlib import Path
from random import shuffle

from sqlalchemy import MetaData, create_engine
from sqlalchemy.sql.elements import quoted_name
from sqlalchemy.sql.expression import func, select
from yaml.representer import Representer

from snowfakery.data_gen_exceptions import DataGenError, DataGenNameError
from snowfakery.plugins import (
    PluginResult,
    PluginResultIterator,
    SnowfakeryPlugin,
    memorable,
)
from snowfakery.utils.files import FileLike, open_file_like
from snowfakery.utils.yaml_utils import SnowfakeryDumper


def _open_db(db_url):
    "Internal function for opening the database up."
    engine = create_engine(db_url)
    metadata = MetaData(bind=engine)
    metadata.reflect(views=True)
    return engine, metadata


def sql_dataset(db_url: str, tablename: str = None, mode="linear", repeat: bool = True):
    "Open the right SQL Dataset iterator based on the params"
    assert db_url
    engine, metadata = _open_db(db_url)
    tables = {
        name: value
        for name, value in metadata.tables.items()
        if not name.startswith("sqlite")
    }
    if tablename:
        table = tables.get(tablename)
        if table is None:
            raise AttributeError(f"Cannot find table: {tablename}")
    elif len(tables) == 0:
        raise Exception("Database does not exist or has no tables in it")
    elif len(tables) == 1:
        table = next(iter(tables.values()))
    elif len(tables) > 1:
        raise Exception(
            f"Database has multiple tables in it and none was selected: {metadata.tables.keys()}"
        )
    if mode == "linear":
        return SQLDatasetLinearIterator(engine, table, repeat)
    elif mode == "shuffle":
        return SQLDatasetRandomPermutationIterator(engine, table, repeat)
    else:
        raise NotImplementedError(f"Unknown mode: {mode}")


class DatasetIteratorBase(PluginResultIterator):
    """Base class for Dataset Iterators

    Subclasses should implement 'self.restart' which puts an iterator into 'self.results'
    """

    def next_result(self):
        return next(self.results)


class SQLDatasetIterator(DatasetIteratorBase):
    def __init__(self, engine, table, repeat):
        self.connection = engine.connect()
        self.table = table
        super().__init__(repeat)
        self.start()

    def start(self):
        self.results = (
            DatasetPluginResult(dict(row))
            for row in self.connection.execute(self.query())
        )

    def close(self):
        self.results = None
        self.connection.close()

    def query(self):
        "Return a SQL Alchemy SELECT statement"
        raise NotImplementedError(f"query method on {self.__class__.__name__}")


class SQLDatasetLinearIterator(SQLDatasetIterator):
    "Iterator that reads a SQL table from top to bottom"

    def query(self):
        return select([self.table])


class SQLDatasetRandomPermutationIterator(SQLDatasetIterator):
    "Iterator that reads a SQL table in random order"

    def query(self):
        return select([self.table]).order_by(func.random())


class CSVDatasetLinearIterator(DatasetIteratorBase):
    def __init__(self, datasource: FileLike, repeat: bool):
        self.cleanup = ExitStack()
        # utf-8-sig and newline="" are for Windows
        self.path, self.file = self.cleanup.enter_context(
            open_file_like(datasource, "r", newline="", encoding="utf-8-sig")
        )

        self.start()
        super().__init__(repeat)

    def start(self):
        self.file.seek(0)
        d = DictReader(self.file)

        plugin_result = self.plugin_result
        self.results = (plugin_result(row) for row in d)

    def close(self):
        self.results = None
        self.cleanup.close()

    def plugin_result(self, row):
        if None in row:
            raise DataGenError(
                f"Your CSV row has more columns than the CSV header:  {row[None]}, {self.path} {self.file}"
            )

        return DatasetPluginResult(row)


class DatasetPluginResult(PluginResult):
    def __getattr__(self, name):
        try:
            return super().__getattr__(name)
        except KeyError:
            raise DataGenNameError(
                f"`{name}` attribute not found. Should be one of {tuple(self.result.keys())}"
            )


class CSVDatasetRandomPermutationIterator(CSVDatasetLinearIterator):
    # This algorithm shuffles a million records without a problem on my laptop.
    # If you needed to scale it up to 40 or 50 times the scale, you could do
    # this instead:
    #   * don't read the whole file into memory. Just figure out where the line
    #     breaks are and shuffle the address of THOSE. Then seek to lines
    #     during parsing
    #
    # To scale even further:
    #
    #   * load the rows or indexes into a SQLite DB. Ask SQlite to generate
    #     another table that randomizes the rows. (haven't decided whether
    #     copying the rows up-front is better)
    #
    #   * segment the file into hundred-thousand-row partitions. Shuffle the
    #     rows in each partition and then pick randomly among the partitions
    #     before grabbing a row
    def start(self):
        self.file.seek(0)
        d = DictReader(self.file)
        rows = [DatasetPluginResult(row) for row in d]
        shuffle(rows)

        self.results = iter(rows)

    def close(self):
        self.results = None


class DatasetBase:
    def __init__(self, *args, **kwargs):
        self.datasets = {}

    def _get_dataset_instance(self, plugin_context, iteration_mode, kwargs):
        filename = plugin_context.field_vars()["template"].filename
        assert filename
        rootpath = Path(filename).parent
        dataset_instance = self._load_dataset(iteration_mode, rootpath, kwargs)
        return dataset_instance

    def _load_dataset(self, iteration_mode, rootpath, kwargs):
        raise NotImplementedError()

    def close(self):
        for dataset in self.datasets.values():
            dataset.close()


class FileDataset(DatasetBase):
    def _load_dataset(self, iteration_mode, rootpath, kwargs):
        dataset = kwargs.get("dataset")
        tablename = kwargs.get("table")
        repeat = kwargs.get("repeat", True)

        with chdir(rootpath):
            if "://" in dataset:
                return sql_dataset(dataset, tablename, iteration_mode, repeat)
            else:
                filename = Path(dataset)

                if not filename.exists():
                    raise FileNotFoundError("File not found:" + str(filename))

                if filename.suffix != ".csv":
                    raise AssertionError(
                        f"Filename extension must be .csv, not {filename.suffix}"
                    )

                if iteration_mode == "linear":
                    return CSVDatasetLinearIterator(filename, repeat)
                elif iteration_mode == "shuffle":
                    return CSVDatasetRandomPermutationIterator(filename, repeat)


class DatasetPluginBase(SnowfakeryPlugin):
    class Functions:
        @memorable
        def iterate(self, **kwargs):
            return self.context.plugin.dataset_impl._get_dataset_instance(
                self.context, "linear", kwargs
            )

        @memorable
        def shuffle(self, **kwargs):
            return self.context.plugin.dataset_impl._get_dataset_instance(
                self.context, "shuffle", kwargs
            )

    def close(self):
        if self.dataset_impl:
            self.dataset_impl.close()
            self.dataset_impl = None


class Dataset(DatasetPluginBase):
    def __init__(self, *args, **kwargs):
        self.dataset_impl = FileDataset()
        super().__init__(*args, **kwargs)


@contextmanager
def chdir(path):
    """Context manager that changes to another directory

    Not thread-safe!!!
    """
    cwd = os.getcwd()
    os.chdir(path)
    try:
        yield
    finally:
        os.chdir(cwd)


SnowfakeryDumper.add_representer(quoted_name, Representer.represent_str)
