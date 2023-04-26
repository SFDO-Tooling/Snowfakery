"""Tools for safely saving and loading pickles using an AllowedList"""

import copyreg
import io
import pickle
import typing as T

import warnings


DispatchDefinition = T.Callable[[T.Any], T.Tuple[type, T.Tuple]]


class RestrictedPickler:
    def __init__(
        self,
        dispatchers: T.Mapping[type, DispatchDefinition],
        _SAFE_CLASSES: T.Set[T.Tuple[str, str]],
    ) -> None:
        self._DISPATCH_TABLE = copyreg.dispatch_table.copy()
        self._DISPATCH_TABLE.update(dispatchers)
        self.RestrictedUnpickler = _get_RestrictedUnpicklerClass(_SAFE_CLASSES)

    def dumps(self, data):
        """Only allow saving "safe" classes"""
        outs = io.BytesIO()
        pickler = pickle.Pickler(outs)
        pickler.dispatch_table = self._DISPATCH_TABLE
        pickler.dump(data)
        return outs.getvalue()

    def loads(self, s):
        """Helper function analogous to pickle.loads()."""
        return self.RestrictedUnpickler(io.BytesIO(s)).load()


class Type_Cannot_Be_Used_With_Random_Reference(T.NamedTuple):
    """This type cannot be unpickled."""

    module: str
    name: str


def _get_RestrictedUnpicklerClass(_SAFE_CLASSES):
    class RestrictedUnpickler(pickle.Unpickler):
        """Safe unpickler with an allowed-list"""

        count = 0

        def find_class(self, module, name):
            # Only allow safe classes from builtins.
            if (module, name) in _SAFE_CLASSES:
                return super().find_class(module, name)
            else:
                # warn first 10 times
                if RestrictedUnpickler.count < 10:
                    warnings.warn(f"Cannot save and refer to {module}, {name}")
                    RestrictedUnpickler.count += 1
                # Return a "safe" object that does nothing.
                return lambda *args: Type_Cannot_Be_Used_With_Random_Reference(
                    module, name
                )

    return RestrictedUnpickler
