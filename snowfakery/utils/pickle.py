"""Tools for safely saving and loading pickles using an AllowedList"""

import copyreg
import io
import pickle
import typing as T

import warnings

from snowfakery.object_rows import NicknameSlot, ObjectReference, ObjectRow

_DISPATCH_TABLE = copyreg.dispatch_table.copy()
_DISPATCH_TABLE[NicknameSlot] = lambda n: (
    ObjectReference,
    (n._tablename, n.allocated_id),
)
_DISPATCH_TABLE[ObjectRow] = lambda v: (
    ObjectRow,
    (v._tablename, v._values),
)


def restricted_dumps(data):
    """Only allow saving "safe" classes"""
    outs = io.BytesIO()
    pickler = pickle.Pickler(outs)
    pickler.dispatch_table = _DISPATCH_TABLE
    pickler.dump(data)
    return outs.getvalue()


class Type_Cannot_Be_Used_With_Random_Reference(T.NamedTuple):
    """This type cannot be unpickled."""

    module: str
    name: str


_SAFE_CLASSES = {
    ("snowfakery.object_rows", "ObjectRow"),
    ("snowfakery.object_rows", "ObjectReference"),
    ("snowfakery.object_rows", "LazyLoadedObjectReference"),
    ("decimal", "Decimal"),
    ("datetime", "date"),
    ("datetime", "datetime"),
    ("datetime", "timedelta"),
    ("datetime", "timezone"),
}


class RestrictedUnpickler(pickle.Unpickler):
    """Safe unpickler with an allowed-list"""

    count = 0

    def find_class(self, module, name):
        # Only allow safe classes from builtins.
        if (module, name) in _SAFE_CLASSES:
            return super().find_class(module, name)
        else:
            # Return a "safe" object that does nothing.
            if RestrictedUnpickler.count < 10:
                warnings.warn(f"Cannot save and refer to {module}, {name}")
                RestrictedUnpickler.count += 1
            return lambda *args: Type_Cannot_Be_Used_With_Random_Reference(module, name)


def restricted_loads(s):
    """Helper function analogous to pickle.loads()."""
    return RestrictedUnpickler(io.BytesIO(s)).load()
