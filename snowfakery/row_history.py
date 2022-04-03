from collections import defaultdict
import typing as T
import sqlite3
import pickle
from random import choices, randint
from copy import deepcopy
from snowfakery.object_rows import ObjectReference, ObjectRow


# TODO:
#   * use static analysis to turn on RowHistory only where relevant
#   * lazy-load referenced row data
#   * figure out just-once + random_reference semantics
#       * can only refer to just_once by nickname
#   * test random_reference of nicknames and just_once/nicknames


class RowHistory:
    def __init__(self):
        self.conn = sqlite3.connect(":memory:")
        self.table_counters = defaultdict(lambda: defaultdict(int))
        self.reset_locals()

    def reset_locals(self):
        """Reset the minimum count that counts as "local" """
        self.local_counters = deepcopy(self.table_counters)

    def save_row(self, tablename: str, nickname: T.Optional[str], row: dict):
        nickname_counters = self.table_counters[tablename]
        sql_tablename = nickname if nickname else tablename

        pk = nickname_counters[sql_tablename]

        if not pk:
            _make_history_table(self.conn, sql_tablename)
        pk += 1
        nickname_counters[sql_tablename] = pk

        self.conn.execute(
            f'INSERT INTO "{sql_tablename}" VALUES (?, ?, ?)',
            (
                pk,
                row["id"],
                pickle.dumps(row),
            ),
        )
        # print("IN SAVE", self.table_counters, id(self.table_counters))

    def read_random_row(
        self, tablename: str, nickname: T.Optional[str], scope: str
    ) -> ObjectRow:
        # print("IN READ", self.table_counters, id(self.table_counters))
        nickname_counters = self.table_counters.get(tablename)
        # print(
        #     "ZZZ2",
        #     len(self.table_counters),
        #     self.table_counters,
        #     nickname_counters,
        #     id(self.table_counters),
        # )
        if not nickname_counters:
            raise AssertionError(f"Cannot find tablename {tablename}")

        if nickname:
            sql_tablename = nickname
            if not nickname_counters.get(sql_tablename):
                raise AssertionError(f"Cannot find nickname {nickname}")
        else:
            # pick which nickname to pull from (including the null nickname)

            # TODO: exclude just_once nicknames
            sql_tablename = choices(
                tuple(nickname_counters.keys()), tuple(nickname_counters.values()), k=1
            )[0]

        if scope == "prior-and-current-iterations":
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
            print("AAA", minpk, maxpk)
            minpk = 1
        print("BBB", minpk, maxpk)

        pk = randint(minpk, maxpk)
        qr = self.conn.execute(
            f'SELECT DATA FROM "{sql_tablename}" WHERE pk=?',
            (pk,),
        )
        first_row = next(qr, None)
        assert first_row

        data = pickle.loads(first_row[0])
        return ObjectRow(tablename, data)


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
