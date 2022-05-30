import typing as T
import sqlite3
from random import randint
from copy import deepcopy
from snowfakery.object_rows import (
    ObjectRow,
    LazyLoadedObjectReference,
)
from snowfakery.utils.pickle import restricted_dumps, restricted_loads
from snowfakery import data_gen_exceptions as exc
import warnings

# TODO:
#   * test random_reference of nicknames and just_once/nicknames


class RowHistory:
    """Remember tables that might be random_reference'd in a database."""

    already_warned = False

    def __init__(self):
        self.conn = sqlite3.connect("")
        self.table_counters = {}
        self.nickname_counters = {}
        self.reset_locals()
        self.nicknames_to_tables = {}

    def reset_locals(self):
        """Reset the minimum count that counts as "local" """
        self.local_counters = deepcopy(self.table_counters)

    def save_row(self, tablename: str, nickname: T.Optional[str], row: dict):
        """Save a row to temporary storage"""
        row_id = row["id"]

        self._ensure_history_table_exists(tablename)

        # keep track of highest ID
        self.table_counters[tablename] = row_id

        if nickname and nickname not in self.nicknames_to_tables:
            self.nicknames_to_tables[nickname] = tablename
            nickname_table = self.nickname_counters.setdefault(tablename, {})
            nickname_table[nickname] = 0

        if nickname:
            self.nickname_counters[tablename][nickname] += 1
            nickname_id = self.nickname_counters[tablename][nickname]
        else:
            nickname_id = None

        # note that this dumps a full object tree
        # that will cause some duplication of data but doing a big
        # "join" across multiple tables would have other costs (even if done lazily).
        # For now this seems best and simplest.
        # The data de-dupling algorithm would be slightly complex and slow.
        data = restricted_dumps(row)
        self.conn.execute(
            f'INSERT INTO "{tablename}" VALUES (?, ?, ?, ?)',
            (row["id"], nickname, nickname_id, data),
        )

    def random_row_reference(self, name: str, scope: str, unique: bool):
        """Find a random row and load it"""
        if scope not in ("prior-and-current-iterations", "current-iteration"):
            raise exc.DataGenError(
                f"Scope must be 'prior-and-current-iterations' or 'current-iteration' not {scope}",
                None,
                None,
            )

        # Next Step: implement "unique" with a Linear Congruent Generator

        if name in self.nicknames_to_tables:
            nickname = name
            tablename = self.nicknames_to_tables[nickname]
        else:
            nickname = None
            tablename = name

        max_id = self.table_counters.get(tablename)
        if not max_id:
            raise exc.DataGenError(
                f"There is no table or nickname `{tablename}` at this point in the recipe."
            )

        if scope == "prior-and-current-iterations":
            if not self.already_warned:
                warnings.warn("Global scope is an experimental feature.")
                self.already_warned = True
            min_id = 1
        else:
            min_id = self.local_counters.get(tablename, 0) + 1
        # if no records can be found in this iteration
        # just look through the whole table.
        #
        # This happens usually when you are referring to just_once
        if max_id <= min_id:
            min_id = 1

        rand_id = randint(min_id, max_id)

        if nickname:
            # nickname rows cannot be lazy-loaded because we need to do a real
            # query to get the 'real id' anyhow

            data = self.load_nicknamed_row(tablename, nickname, rand_id)
            return ObjectRow(tablename, data)
        else:
            # if nickname is not specified, we don't need to read anything
            # from DB until a property is asked for.
            return LazyLoadedObjectReference(tablename, rand_id, tablename)

    def load_row(self, tablename: str, row_id: int):
        """Load a row from the DB by row_id/object_id"""
        qr = self.conn.execute(
            f'SELECT DATA FROM "{tablename}" WHERE id=?',
            (row_id,),
        )
        first_row = next(qr, None)
        assert first_row, f"Something went wrong: we cannot find {tablename}: {row_id}"

        return restricted_loads(first_row[0])

    def load_nicknamed_row(self, tablename: str, nickname: str, nickname_id: int):
        """Find a nicknamed row by its nickname_id"""
        qr = self.conn.execute(
            f'SELECT DATA FROM "{tablename}" WHERE nickname=? AND nickname_id=?',
            (nickname, nickname_id),
        )
        first_row = next(qr, None)
        assert (
            first_row
        ), f"Something went wrong: we cannot find {tablename}: {nickname} : {nickname_id}"

        return restricted_loads(first_row[0])

    def _ensure_history_table_exists(self, tablename):
        if tablename not in self.table_counters:  # newly discovered table
            _make_history_table(self.conn, tablename)
            self.table_counters[tablename] = 0


def _make_history_table(conn, tablename):
    """Make a history table"""

    c = conn.cursor()
    c.execute(
        f'CREATE TABLE "{tablename}" (id INTEGER NOT NULL UNIQUE , nickname VARCHAR, nickname_id INTEGER, data VARCHAR NOT NULL)'
    )
    # helps with sparsely scattered nicknames. Of debatable value. Can speed up benchmarks
    # but hard to see it in real recipes.
    c.execute(
        f'CREATE UNIQUE INDEX "{tablename}_nickname_id" ON "{tablename}" (nickname, nickname_id);'
    )
