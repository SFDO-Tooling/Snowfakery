from pathlib import Path
from csv import DictReader
from contextlib import contextmanager
import os
from random import shuffle

from sqlalchemy import create_engine, MetaData
from sqlalchemy.sql.expression import func, select
from sqlalchemy.sql.elements import quoted_name

from yaml.representer import Representer

from snowfakery.plugins import SnowfakeryPlugin, PluginResult
from snowfakery.utils.yaml_utils import SnowfakeryDumper


def _open_db(db_url):
    "Internal function for opening the database up."
    engine = create_engine(db_url)
    metadata = MetaData(bind=engine)
    metadata.reflect(views=True)
    return engine, metadata


def sql_dataset(db_url: str, tablename: str = None, mode="linear"):
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
        return SQLDatasetLinearIterator(engine, table)
    elif mode == "shuffle":
        return SQLDatasetRandomPermutationIterator(engine, table)
    else:
        raise NotImplementedError(f"Unknown mode: {mode}")


class DatasetIteratorBase:
    """Base class for Dataset Iterators

    Subclasses should implement 'self.restart' which puts an iterator into 'self.results'
    """

    def __next__(self):
        try:
            return next(self.results)
        except StopIteration:
            self.restart()

    def start(self):
        "Initialize the iterator in self.results."
        raise NotImplementedError(f"start method on {self.__class__.__name__}")

    def restart(self):
        "Restart the iterator by assigning to self.results"
        self.start()

    def close(self):
        "Subclasses should implement this if they need to clean up resources"
        pass  # pragma: no cover


class SQLDatasetIterator(DatasetIteratorBase):
    def __init__(self, engine, table):
        self.connection = engine.connect()
        self.table = table
        self.start()

    def start(self):
        self.results = (
            PluginResult(dict(row)) for row in self.connection.execute(self.query())
        )

    def close(self):
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
    def __init__(self, datasource: Path):
        self.datasource = datasource
        self.file = open(self.datasource, newline="", encoding="utf-8")
        self.start()

    def start(self):
        self.file.seek(0)
        d = DictReader(self.file)
        self.results = (PluginResult(row) for row in d)

    def close(self):
        self.file.close()


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
        rows = [PluginResult(row) for row in d]
        shuffle(rows)

        self.results = iter(rows)


class DatasetBase:
    def __init__(self, *args, **kwargs):
        self.datasets = {}

    def _iterate(self, plugin, iteration_mode, kwargs):
        self.context = plugin.context
        key = self._get_key(kwargs)
        dataset_instance = self._get_dataset_instance(key, iteration_mode, kwargs)
        rc = next(dataset_instance, None)
        if not rc:
            dataset_instance.start()
            rc = next(dataset_instance, None)

        assert rc is not None
        return rc

    def _get_key(self, kwargs):
        dataset = kwargs.get("dataset")
        tablename = kwargs.get("table")
        uniq_name = kwargs.get("name") or self.context.unique_context_identifier()
        return (dataset, tablename, uniq_name)

    def _get_dataset_instance(self, key, iteration_mode, kwargs):
        dataset_instance = self.datasets.get(key)
        if not dataset_instance:
            filename = self.context.field_vars()["template"].filename
            assert filename
            rootpath = Path(filename).parent
            dataset_instance = self.datasets[key] = self._load_dataset(
                iteration_mode, rootpath, kwargs
            )
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

        with chdir(rootpath):
            if "://" in dataset:
                return sql_dataset(dataset, tablename, iteration_mode)
            else:
                filename = Path(dataset)

                if not filename.exists():
                    raise FileNotFoundError("File not found:" + str(filename))

                if filename.suffix != ".csv":
                    raise AssertionError(
                        f"Filename extension must be .csv, not {filename.suffix}"
                    )

                if iteration_mode == "linear":
                    return CSVDatasetLinearIterator(filename)
                elif iteration_mode == "shuffle":
                    return CSVDatasetRandomPermutationIterator(filename)


class DatasetPluginBase(SnowfakeryPlugin):
    class Functions:
        def iterate(self, **kwargs):
            return self.context.plugin.dataset_impl._iterate(self, "linear", kwargs)

        def shuffle(self, **kwargs):
            return self.context.plugin.dataset_impl._iterate(self, "shuffle", kwargs)


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
