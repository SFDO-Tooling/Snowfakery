import typing as T
import sqlite3
from random import randint
from copy import deepcopy
from snowfakery.object_rows import (
    LazyLoadedObjectReference,
)
from snowfakery.utils.pickle import restricted_dumps, restricted_loads
from snowfakery import data_gen_exceptions as exc
import warnings


class RowHistory:
    """Remember tables that might be random_reference'd in a database."""

    already_warned = False

    def __init__(self, table_counters: T.Mapping):
        self.conn = sqlite3.connect("")
        self.table_counters = dict(table_counters)
        self.nickname_counters = {}
        self.reset_locals()
        self.tablename_for_nickname = {}
        self.tables_already_created = set()

    def reset_locals(self):
        """Reset the minimum count that counts as "local" """
        self.local_counters = deepcopy(self.table_counters)

    def save_row(self, tablename: str, nickname: T.Optional[str], row: dict):
        """Save a row to temporary storage"""
        row_id = row["id"]

        self._ensure_history_table_exists(tablename)

        # keep track of highest ID
        self.table_counters[tablename] = row_id

        if nickname:
            nickname_id = self._get_nickname_id(tablename, nickname)
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
            (row_id, nickname, nickname_id, data),
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

        if name in self.tablename_for_nickname:
            nickname = name
            tablename = self.tablename_for_nickname[nickname]
            max_id = self.nickname_counters[nickname]
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

        if nickname:
            # find a random nickname'd row by its nickname_id
            nickname_id = randint(min_id, max_id)
            row_id = self.find_row_id_for_nickname_id(tablename, nickname, nickname_id)
        else:
            # find a random row
            row_id = randint(min_id, max_id)

        return LazyLoadedObjectReference(tablename, row_id, tablename)

    def load_row(self, tablename: str, row_id: int):
        """Load a row from the DB by row_id/object_id"""
        qr = self.conn.execute(
            f'SELECT DATA FROM "{tablename}" WHERE id=?',
            (row_id,),
        )
        first_row = next(qr, None)
        assert first_row, f"Something went wrong: we cannot find {tablename}: {row_id}"

        return restricted_loads(first_row[0])

    def find_row_id_for_nickname_id(
        self, tablename: str, nickname: str, nickname_id: int
    ):
        #     """Find a nicknamed row by its nickname_id"""
        qr = self.conn.execute(
            f'SELECT id FROM "{tablename}" WHERE nickname=? AND nickname_id=?',
            (nickname, nickname_id),
        )
        first_row = next(qr, None)
        assert (
            first_row
        ), f"Something went wrong: we cannot find {tablename}: {nickname} : {nickname_id}"

        return first_row[0]

    def _ensure_history_table_exists(self, tablename):
        if tablename not in self.tables_already_created:  # newly discovered table
            _make_history_table(self.conn, tablename)
            self.table_counters[tablename] = 0
            self.tables_already_created.add(tablename)

    def _get_nickname_id(self, tablename: str, nickname: str):
        """Get a unique auto-incrementing identifier for a new row"""
        if nickname not in self.tablename_for_nickname:
            self.tablename_for_nickname[nickname] = tablename
            self.nickname_counters[nickname] = 0

        self.nickname_counters[nickname] += 1
        return self.nickname_counters[nickname]


def _make_history_table(conn, tablename):
    """Make a history table"""

    c = conn.cursor()
    c.execute(
        f'CREATE TABLE "{tablename}" (id INTEGER NOT NULL UNIQUE, nickname VARCHAR, nickname_id INTEGER, data VARCHAR NOT NULL)'
    )
    # helps with sparsely scattered nicknames. Of debatable value. Can speed up benchmarks
    # but hard to see it in real recipes.
    c.execute(
        f'CREATE UNIQUE INDEX "{tablename}_nickname_id" ON "{tablename}" (nickname, nickname_id);'
    )
