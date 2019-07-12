from typing import TypeVar, Generic

KT = TypeVar('KT')  # Key type.
VT = TypeVar('VT')  # Value type.


class FrozenDict(dict, Generic[KT, VT]):
    """
    A dictionary which cannot be changed a la frozenset.

    Implementation from [PEP-351](https://www.python.org/dev/peps/pep-0351/).
    """

    def __hash__(self):
        hash_ = 0
        for key, value in self.items():
            hash_ ^= hash((key, value))
        return hash_

    def _immutable(self, *args, **kws):
        raise TypeError('A FrozenDict instance cannot be changed')

    __setitem__ = _immutable
    __delitem__ = _immutable
    clear = _immutable
    update = _immutable
    setdefault = _immutable
    pop = _immutable
    popitem = _immutable


class FrozenList(tuple, Generic[VT]):
    """A list that cannot be changed. `FrozenList[VT]` is equal to saying `Tuple[VT, ...]`."""
    pass


frozendict = FrozenDict
frozenlist = FrozenList
