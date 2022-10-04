from enum import Enum, auto

import yaml
import snowfakery  # noqa
from .utils.yaml_utils import SnowfakeryDumper
from contextvars import ContextVar

IdManager = "snowfakery.data_generator_runtime.IdManager"
RowHistoryCV = ContextVar("RowHistory")


class ObjectRow:
    """Represents a single row

    Uses __getattr__ so that the template evaluator can use dot-notation."""

    yaml_loader = yaml.SafeLoader
    yaml_dumper = SnowfakeryDumper
    yaml_tag = "!snowfakery_objectrow"

    # be careful changing these slots because these objects must be serializable
    # to YAML and JSON
    __slots__ = ["_tablename", "_values", "_child_index"]

    def __init__(self, tablename, values=(), index=0):
        self._tablename = tablename
        self._values = values
        self._child_index = index

    def __getattr__(self, name):
        try:
            return self._values[name]
        except KeyError:
            raise AttributeError(name)

    # prefer this to .id or _values["id"] so we can
    # one day move away from having "id" in the user's
    # namespace
    @property
    def _id(self):
        return self._values["id"]

    def __str__(self):
        return str(self.id)

    def __repr__(self):
        try:
            return f"<ObjectRow {self._tablename} {self.id}>"
        except Exception:
            return super().__repr__()

    def __getstate__(self):
        """Get the state of this ObjectRow for serialization.

        Do not include related ObjectRows because circular
        references in serialization formats cause problems."""
        values = {k: v for k, v in self._values.items() if not isinstance(v, ObjectRow)}
        return {"_tablename": self._tablename, "_values": values}

    def __setstate__(self, state):
        for slot, value in state.items():
            setattr(self, slot, value)


class ObjectReference(yaml.YAMLObject):
    def __init__(self, tablename: str, id: int):
        self._tablename = tablename
        self.id = id


class LazyLoadedObjectReference(ObjectReference):
    _data = None

    def __init__(
        self,
        tablename: str,
        id: int,
        sql_tablename: str,
    ):
        self._tablename = tablename
        self.sql_tablename = sql_tablename
        self.id = id

    def __getattr__(self, attrname):
        if attrname.endswith("__"):  # pragma: no cover
            raise AttributeError(attrname)
        if self._data is None:
            row_history = RowHistoryCV.get()
            self._data = row_history.load_row(self.sql_tablename, self.id)
        return self._data[attrname]


class SlotState(Enum):
    """The current state of a NicknameSlot.

    UNUSED=empty, ALLOCATED=referenced, CONSUMED=object generated"""

    UNUSED = auto()
    ALLOCATED = auto()
    CONSUMED = auto()


class NicknameSlot(ObjectReference):
    """A slot that represents a Nickname or Tablename"""

    _tablename: str
    id_manager: IdManager
    allocated_id: int = None

    def __init__(self, tablename: str, id_manager: IdManager):
        self._tablename = tablename
        self.id_manager = id_manager

    @property
    def id(self):
        "Get an id corresponding to this slot. Generate one if necessary."
        if self.allocated_id is None:
            self.allocated_id = self.id_manager.generate_id(self._tablename)
        return self.allocated_id

    def consume_slot(self):
        "Mark a slot as filled by an object and return its id for use by the object."
        rc = self.allocated_id
        self.allocated_id = SlotState.CONSUMED
        return rc

    @property
    def status(self):
        "Is the slot empty/unreferenced, allocated/referenced or consumed/used"
        if self.allocated_id is None:
            return SlotState.UNUSED
        elif isinstance(self.allocated_id, int):
            return SlotState.ALLOCATED
        elif self.allocated_id == SlotState.CONSUMED:
            return SlotState.CONSUMED

    def __repr__(self):
        return f"<NicknameSlot {self._tablename} {self.status} {self.allocated_id}>"
