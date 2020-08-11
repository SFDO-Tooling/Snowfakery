from pathlib import Path
from csv import DictReader
from contextlib import contextmanager
import os
from random import shuffle

from sqlalchemy import create_engine, MetaData
from sqlalchemy.sql.expression import func, select
from sqlalchemy.sql.elements import quoted_name

import yaml
from yaml.representer import Representer

from snowfakery.plugins import SnowfakeryPlugin, PluginResult


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
    elif mode == "permute":
        return SQLDatasetRandomPermutationIterator(engine, table)
    else:
        raise NotImplementedError()


class DatasetIteratorBase:
    """Base class for Dataset Iterators

    Subclasses should implement 'self.restart' which puts an iterator into 'self.results'
    """

    def __iter__(self):
        return self

    def __next__(self):
        try:
            return next(self.results)
        except StopIteration:
            if self.should_restart:
                self.start()
            else:
                raise StopIteration("Dataset is finished")

    def start(self):
        "Initialize the iterator."
        self.restart()

    def restart(self):
        raise NotImplementedError()

    def stop(self):
        raise NotImplementedError()


class SQLDatasetLinearIterator(DatasetIteratorBase):
    "Iterator that reads a SQL table from top to bottom"

    def __init__(self, engine, table, should_restart=True):
        self.should_restart = should_restart
        self.engine = engine
        self.table = table
        self.start()

    def start(self):
        self.results = (
            PluginResult(dict(row)) for row in self.engine.execute(select([self.table]))
        )

    # TODO: runtime doesn't call this yet
    def stop(self):
        self.engine.close()


class SQLDatasetRandomPermutationIterator(SQLDatasetLinearIterator):
    "Iterator that reads a SQL table in random order"

    def start(self):
        self.results = (
            PluginResult(dict(row))
            for row in self.engine.execute(select([self.table]).order_by(func.random()))
        )


class CSVDatasetLinearIterator(DatasetIteratorBase):
    def __init__(self, datasource: Path, should_restart: bool = True):
        self.datasource = datasource
        self.file = open(self.datasource)
        self.should_restart = should_restart
        self.start()

    def start(self):
        self.file.seek(0)
        d = DictReader(self.file)
        self.results = (PluginResult(row) for row in d)


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


class Dataset(SnowfakeryPlugin):
    class Functions:
        record_sets = {}

        def iterate(self, *args, **kwargs):
            return self._iterate(*args, **kwargs, iteration_mode="linear")

        def permute(self, *args, **kwargs):
            return self._iterate(*args, **kwargs, iteration_mode="permute")

        def _iterate(self, dataset, tablename=None, name=None, iteration_mode="linear"):
            name = name or self.context.field_vars()["template"].id
            key = (dataset, tablename, name)
            dataset_instance = self.record_sets.get(key)
            if not dataset_instance:
                filename = self.context.field_vars()["template"].filename
                if filename:
                    rootpath = Path(filename).parent
                else:
                    rootpath = "."
                dataset_instance = self.record_sets[key] = self._load_dataset(
                    dataset, tablename, rootpath, iteration_mode
                )
            rc = next(dataset_instance, None)
            if not rc:
                dataset_instance.start()
                rc = next(dataset_instance, None)

            assert rc is not None
            return rc

        def _load_dataset(self, dataset, tablename, rootpath, iteration_mode):
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
                    elif iteration_mode == "permute":
                        return CSVDatasetRandomPermutationIterator(filename)


@contextmanager
def chdir(path):
    """Context manager that changes to another directory

    Not thread-safe!!!
    """
    if not path:
        yield
        return
    cwd = os.getcwd()
    os.chdir(path)
    try:
        yield
    finally:
        os.chdir(cwd)


yaml.SafeDumper.add_representer(quoted_name, Representer.represent_str)
