import sqlite3
import typing as T
import warnings
from collections import defaultdict
from copy import deepcopy
from random import randint

from snowfakery import data_gen_exceptions as exc
from snowfakery.object_rows import LazyLoadedObjectReference, ObjectReference, ObjectRow
from snowfakery.plugins import PluginResultIterator
from snowfakery.utils.pickle import restricted_dumps, restricted_loads
from snowfakery.utils.randomized_range import UpdatableRandomRange


class RowHistory:
    """Remember tables that might be random_reference'd in a database."""

    already_warned = False

    def __init__(
        self,
        table_counters: T.Mapping,
        tables_to_keep_history_for: T.Iterable[str],
        tablename_for_nickname: T.Mapping[str, str],
    ):
        self.conn = sqlite3.connect("")
        self.table_counters = dict(table_counters)
        self.nickname_counters = defaultdict(int)
        self.reset_locals()
        # the pattern is A -> A means A is a table
        #                B -> A means B is a nickname and A is a table
        #
        self.nickname_to_tablename = {
            nick: table
            for nick, table in tablename_for_nickname.items()
            if table != nick
        }
        for table in tables_to_keep_history_for:
            _make_history_table(self.conn, table)

    def reset_locals(self):
        """Reset the minimum count that counts as "local" """
        self.local_counters = deepcopy(self.table_counters)

    def save_row(self, tablename: str, nickname: T.Optional[str], row: dict):
        """Save a row to temporary storage"""
        row_id = row["id"]

        # keep track of highest ID
        self.table_counters[tablename] = row_id

        if nickname:
            nickname_id = self._get_nickname_id(tablename, nickname)
            self.table_counters[nickname] = nickname_id
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

    def random_row_reference(self, name: str, scope: str, randomizer_func: callable):
        """Find a random row and load it"""
        if scope not in ("prior-and-current-iterations", "current-iteration"):
            raise exc.DataGenError(
                f"Scope must be 'prior-and-current-iterations' or 'current-iteration' not {scope}",
                None,
                None,
            )

        # Next Step: implement "unique" with a Linear Congruent Generator

        if name in self.nickname_to_tablename:
            nickname = name
            tablename = self.nickname_to_tablename[nickname]
            max_id = self.nickname_counters[nickname]
        else:
            nickname = None
            tablename = name
            max_id = self.table_counters.get(tablename)

        if not max_id:
            raise exc.DataGenError(
                f"There is no table or nickname `{nickname or tablename}` at this point in the recipe."
            )

        if scope == "prior-and-current-iterations":
            if not self.already_warned:
                warnings.warn("Global scope is an experimental feature.")
                self.already_warned = True
            min_id = 1
        elif nickname:
            min_id = self.local_counters.get(nickname, 0) + 1
        else:
            min_id = self.local_counters.get(tablename, 0) + 1
        # if no records can be found in this iteration
        # just look through the whole table.
        #
        # This happens usually when you are referring to just_once
        if max_id < min_id:
            min_id = 1

        if nickname:
            # find a random nickname'd row by its nickname_id
            nickname_id = randomizer_func(min_id, max_id)
            row_id = self.find_row_id_for_nickname_id(tablename, nickname, nickname_id)
        else:
            # find a random row
            row_id = randomizer_func(min_id, max_id)

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

    def _get_nickname_id(self, tablename: str, nickname: str):
        """Get a unique auto-incrementing nickname identifier for a new row"""
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


class RandomReferenceContext(PluginResultIterator):
    # initialize the object's state.
    rng = None

    def __init__(
        self,
        row_history: RowHistory,
        to: str,
        scope: str = "current-iteration",
        unique: bool = False,
    ):
        self.row_history = row_history
        self.to = to
        self.scope = scope
        self.unique = unique
        if unique:
            self.random_func = self.unique_random
        else:
            self.random_func = randint

    def next(self) -> T.Union[ObjectReference, ObjectRow]:
        try:
            return self.row_history.random_row_reference(
                self.to, self.scope, self.random_func
            )
        except StopIteration as e:
            if self.random_func == self.unique_random:
                raise exc.DataGenError(
                    f"Cannot find an unused `{self.to}`` to link to"
                ) from e
            else:  # pragma: no cover
                raise e

    def unique_random(self, a, b):
        """Goal: use an Uniquifying RNG until all of its values have been
        used up, then make a new one, with higher values.

        e.g. random_range(1,5) then random_range(5, 10)

        The parent might call it like:
        unique_random(1,2) -> random_range(1,3) -> 2
        unique_random(1,4) -> random_range(1,3) -> 1
        unique_random(1,6) -> random_range(3,7) -> 5  # reset
        unique_random(1,8) -> random_range(3,7) -> 3
        unique_random(1,10) -> random_range(3,7) -> 4
        unique_random(1,12) -> random_range(3,7) -> 6
        unique_random(1,14) -> random_range(7,14) -> 13 # reset
        ...
        """
        b += 1  # randomizer_func uses top-inclusive semantics,
        # random_range uses top-exclusive semantics
        if self.rng is None:
            self.rng = UpdatableRandomRange(a, b)
        else:
            self.rng.set_new_range(a, b)
        return next(self.rng)
