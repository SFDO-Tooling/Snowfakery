import copyreg
import io
import typing as T
import sqlite3
import pickle
from random import randint
from copy import deepcopy
from snowfakery.object_rows import (
    NicknameSlot,
    ObjectRow,
    ObjectReference,
    LazyLoadedObjectReference,
)
import warnings

# TODO:
#   * test random_reference of nicknames and just_once/nicknames
#   * single table per sobject
#   * nickname field
#   * "skinny" objects when random_referencing obj
#   * "fat" object when random_referenciing nickname.
#       * select from objname where pk >= $randnum and nickname = $nickname order by randnum


class RowHistory:
    def __init__(self):
        self.conn = sqlite3.connect("")
        self.table_counters = {}
        self.reset_locals()
        self.nicknames_to_tables = {}

    def reset_locals(self):
        """Reset the minimum count that counts as "local" """
        self.local_counters = deepcopy(self.table_counters)

    def save_row(self, tablename: str, nickname: T.Optional[str], row: dict):
        pk = self.table_counters.setdefault(tablename, 0)
        if not pk:  # new table
            _make_history_table(self.conn, tablename)
            # nickname_counters[None] = 0
        pk += 1
        self.table_counters[tablename] = pk
        if nickname and nickname not in self.nicknames_to_tables:
            self.nicknames_to_tables[nickname] = tablename

        # pk = nickname_counters.setdefault(nickname, 0) + 1
        # nickname_counters[nickname] = pk

        # TODO: think about whether it is okay to save trees of objects or not.
        data = restricted_dumps(row)
        self.conn.execute(
            f'INSERT INTO "{tablename}" VALUES (?, ?, ?)',
            (row["id"], nickname, data),
        )

    def random_row_reference(self, name: str, scope: str):
        # print("IN READ", self.table_counters, id(self.table_counters))
        if name in self.nicknames_to_tables:
            nickname = name
            tablename = self.nicknames_to_tables[nickname]
        else:
            nickname = None
            tablename = name

        maxpk = self.table_counters.get(tablename)
        if not maxpk:
            raise AssertionError(f"There is no table named {tablename}")

        if scope == "prior-and-current-iterations":
            warnings.warn("Global scope is an experimental feature.")
            minpk = 1
        else:
            minpk = self.local_counters.get(tablename, 0) + 1
        # maxpk = nickname_counters[nickname]

        # if no records can be found in this iteration
        # just look through the whole table.
        #
        # This happens usually when you are referring to just_once
        if maxpk <= minpk:
            minpk = 1

        # TODO: think is this right? PK and ID are not necessarily
        #       the same in the case where a nickname is indexed
        #       but its underlying table is not.
        rand_id = randint(minpk, maxpk)

        if nickname:
            # nickname rows cannot be lazy-loaded because we need to do a real
            # query to get the 'id' anyhow

            # the rand_id is just an approximation.
            return self.load_nicknamed_row(tablename, nickname, rand_id)
        else:
            # if nickname is specified, load it eagerly because we need 'id'
            return LazyLoadedObjectReference(tablename, rand_id, tablename)

    def load_row(self, tablename: str, _id: int):
        qr = self.conn.execute(
            f'SELECT DATA FROM "{tablename}" WHERE id=?',
            (_id,),
        )
        first_row = next(qr, None)
        assert first_row

        return restricted_loads(first_row[0])

    def load_nicknamed_row(self, tablename: str, nickname: str, _id: int):
        # find the closest nicknamed row
        qr = self.conn.execute(
            f'SELECT DATA FROM "{tablename}" WHERE nickname = ? AND id >= ? ORDER BY id LIMIT 1',
            (nickname, _id),
        )
        first_row = next(qr, None)

        if not first_row:
            qr = self.conn.execute(
                f'SELECT DATA FROM "{tablename}" WHERE nickname = ? AND id <= ? ORDER BY id DESC LIMIT 1',
                (nickname, _id),
            )
            first_row = next(qr, None)

        assert first_row

        return ObjectRow(tablename, restricted_loads(first_row[0]))


def _make_history_table(conn, tablename):
    c = conn.cursor()
    c.execute(f'DROP TABLE IF EXISTS "{tablename}"')
    c.execute(
        f'CREATE TABLE "{tablename}" (id INTEGER NOT NULL UNIQUE , nickname VARCHAR, data VARCHAR NOT NULL)'
    )
    c.execute(
        f'CREATE UNIQUE INDEX "{tablename}_nickname_id" ON "{tablename}" (nickname, id);'
    )


def _default(val):
    if isinstance(val, (ObjectRow, ObjectReference)):
        return (val._tablename, val.id)
    else:
        return val


NOOP = object()

_SAFE_CLASSES = {
    ("snowfakery.object_rows", "ObjectRow"): NOOP,
    ("snowfakery.object_rows", "ObjectReference"): NOOP,
    # ("decimal", "Decimal"): NOOP,
}
DISPATCH_TABLE = copyreg.dispatch_table.copy()
DISPATCH_TABLE[NicknameSlot] = lambda n: (
    ObjectReference,
    (n._tablename, n.allocated_id),
)


def restricted_dumps(data):
    outs = io.BytesIO()
    pickler = pickle.Pickler(outs)
    pickler.dispatch_table = DISPATCH_TABLE
    pickler.dump(data)
    return outs.getvalue()


class Type_Cannot_Be_Used_With_Random_Reference(T.NamedTuple):
    name: str


class RestrictedUnpickler(pickle.Unpickler):
    def find_class(self, module, name):
        # Only allow safe classes from builtins.
        transformer = _SAFE_CLASSES.get((module, name))
        if transformer is NOOP:
            return super().find_class(module, name)
        elif transformer:
            return super().find_class(*transformer)

        # Forbid everything else.
        return lambda *args: Type_Cannot_Be_Used_With_Random_Reference(name)
        # raise pickle.UnpicklingError("global '%s.%s' is forbidden" % (module, name))


def restricted_loads(s):
    """Helper function analogous to pickle.loads()."""
    return RestrictedUnpickler(io.BytesIO(s)).load()
