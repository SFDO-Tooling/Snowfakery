from collections import defaultdict
import typing as T
import sqlite3
import pickle
from random import choices, randint
from copy import deepcopy
from snowfakery.object_rows import (
    ObjectRow,
    ObjectReference,
    LazyLoadedObjectReference,
)
import warnings

# TODO:
#   * figure out just-once + random_reference semantics
#       * can only refer to just_once by nickname
#   * test random_reference of nicknames and just_once/nicknames


class RowHistory:
    def __init__(self):
        self.conn = sqlite3.connect(":memory:")
        self.table_counters = defaultdict(lambda: defaultdict(int))
        self.reset_locals()
        self.nicknames_to_tables = {}

    def reset_locals(self):
        """Reset the minimum count that counts as "local" """
        self.local_counters = deepcopy(self.table_counters)

    def save_row(self, tablename: str, nickname: T.Optional[str], row: dict):
        nickname_counters = self.table_counters[tablename]
        if nickname:
            if nickname not in self.nicknames_to_tables:
                self.nicknames_to_tables[nickname] = tablename
            sql_tablename = nickname
        else:
            sql_tablename = tablename

        pk = nickname_counters[sql_tablename]

        if not pk:
            _make_history_table(self.conn, sql_tablename)
        pk += 1
        nickname_counters[sql_tablename] = pk

        # TODO: think about whether it is okay to save trees of objects or not.
        self.conn.execute(
            f'INSERT INTO "{sql_tablename}" VALUES (?, ?, ?)',
            (
                pk,
                row["id"],
                pickle.dumps(row),
            ),
        )

    def random_row_reference(self, name: str, scope: str):
        # print("IN READ", self.table_counters, id(self.table_counters))
        if name in self.nicknames_to_tables:
            nickname = name
            tablename = self.nicknames_to_tables[nickname]
        else:
            nickname = None
            tablename = name

        nickname_counters = self.table_counters.get(tablename)
        # print(
        #     "ZZZ2",
        #     len(self.table_counters),
        #     self.table_counters,
        #     nickname_counters,
        #     id(self.table_counters),
        # )
        if not nickname_counters:
            raise AssertionError(f"There is no table named {tablename}")

        if nickname:
            sql_tablename = nickname
        else:
            # pick which nickname to pull from (including the null nickname)

            # TODO: exclude just_once nicknames
            sql_tablename = choices(
                tuple(nickname_counters.keys()), tuple(nickname_counters.values()), k=1
            )[0]

        if scope == "prior-and-current-iterations":
            warnings.warn("Global scope is an experimental feature.")
            minpk = 1
        else:
            relevant_name = nickname or tablename
            minpk = self.local_counters[tablename].get(relevant_name, 0) + 1
        maxpk = nickname_counters[sql_tablename]

        # if no records can be found in this iteration
        # just look through the whole table.
        #
        # This happens usually when you are referring to just_once
        if maxpk <= minpk:
            minpk = 1

        pk = randint(minpk, maxpk)

        # return ObjectRow(tablename, self.read_random_row(sql_tablename, pk))
        return LazyLoadedObjectReference(tablename, pk, sql_tablename)

    def read_random_row(self, sql_tablename: str, pk: int):
        qr = self.conn.execute(
            f'SELECT DATA FROM "{sql_tablename}" WHERE pk=?',
            (pk,),
        )
        first_row = next(qr, None)
        assert first_row

        return pickle.loads(first_row[0])


def _make_history_table(conn, tablename):
    c = conn.cursor()
    c.execute(f'DROP TABLE IF EXISTS "{tablename}"')
    c.execute(
        f'CREATE TABLE "{tablename}" (pk INTEGER NOT NULL UNIQUE, id INTEGER NOT NULL , data VARCHAR NOT NULL)'
    )


def _default(val):
    if isinstance(val, (ObjectRow, ObjectReference)):
        return (val._tablename, val.id)
    else:
        return val
