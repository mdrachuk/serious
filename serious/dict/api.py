from __future__ import annotations

from dataclasses import dataclass
from typing import TypeVar, Type, Generic, List, Collection, Dict, Iterable, Any, Mapping

from serious.preconditions import _check_isinstance, _check_is_dataclass
from serious.serialization import SeriousSerializer

T = TypeVar('T')


@dataclass(frozen=True)
class Dumping:
    pass


@dataclass(frozen=True)
class Loading:
    allow_missing: bool = False
    allow_unexpected: bool = False


class DictSchema(Generic[T]):

    def __init__(self, cls: Type[T], dump: Dumping, load: Loading):
        self._cls = _check_is_dataclass(cls)
        self._dump = dump
        self._load = load
        self._serializer = SeriousSerializer(cls, self._load.allow_missing, self._load.allow_unexpected)

    def dump(self, o: T) -> Dict[str, Any]:
        _check_isinstance(o, self._cls)
        return self._serializer.dump(o)

    def dump_many(self, items: Collection[T]) -> List[Dict[str, Any]]:
        return [self._serializer.dump(_check_isinstance(o, self._cls)) for o in items]

    def load(self, data: Dict[str, Any]) -> T:
        return self._from_dict(data)

    def load_many(self, items: Iterable[Dict[str, Any]]) -> List[T]:
        return [self._from_dict(each) for each in items]

    def _from_dict(self, data: Mapping):
        return self._serializer.load(data)


def dict_schema(cls: Type[T], *,
                allow_missing: bool = Loading.allow_missing,
                allow_unexpected: bool = Loading.allow_unexpected) -> DictSchema[T]:
    dumping = Dumping()
    loading = Loading(allow_missing=allow_missing, allow_unexpected=allow_unexpected)
    return DictSchema(cls, load=loading, dump=dumping)
