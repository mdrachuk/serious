from dataclasses import dataclass, is_dataclass
from typing import TypeVar, Type, Generic, List, Collection, Dict, Iterable, Any, Mapping

from serious.serialization import SeriousSerializer

T = TypeVar('T')


@dataclass(frozen=True)
class Dumping:

    @classmethod
    def defaults(cls):
        return cls()


@dataclass(frozen=True)
class Loading:
    allow_missing: bool = False
    allow_unexpected: bool = False

    @classmethod
    def defaults(cls):
        return cls()


def _check_isinstance(value, cls):
    if not isinstance(value, cls):
        raise Exception(f'Got "{value}" when expecting a "{cls}" instance.')
    return value


class DictSchema(Generic[T]):

    def __init__(self, cls: Type[T], dump: Dumping, load: Loading):
        if not is_dataclass(cls):
            raise Exception('Serious can only operate on dataclasses for now.')
        self._cls = cls
        self._dump = dump
        self._load = load
        self._serializer = SeriousSerializer(cls, self._load.allow_missing, self._load.allow_unexpected)

    def dump(self, o: T) -> Dict[str, Any]:
        _check_isinstance(o, self._cls)
        return self._serializer.dump(o)

    def dump_all(self, items: Collection[T]) -> List[Dict[str, Any]]:
        return [self._serializer.dump(_check_isinstance(o, self._cls)) for o in items]

    def load(self, data: Dict[str, Any]) -> T:
        return self._from_dict(data)

    def load_all(self, items: Iterable[Dict[str, Any]]) -> List[T]:
        return [self._from_dict(each) for each in items]

    def _from_dict(self, data: Mapping):
        return self._serializer.load(data)


def schema(cls: Type[T],
           dump: Dumping = Dumping.defaults(),
           load: Loading = Loading.defaults()) -> DictSchema[T]:
    return DictSchema(cls, dump, load)
