from __future__ import annotations

from dataclasses import dataclass
from typing import TypeVar, Type, Generic, List, Collection, Dict, Iterable, Any, Mapping

from serious.descriptors import describe, TypeDescriptor
from serious.field_serializers import FieldSerializer, field_serializers
from serious.preconditions import _check_is_instance, _check_is_dataclass
from serious.schema import SeriousSchema

T = TypeVar('T')


@dataclass(frozen=True)
class _Loading:
    allow_missing: bool = False
    allow_unexpected: bool = False


@dataclass(frozen=True)
class _Dumping:
    pass


@dataclass(frozen=True)
class _Config:
    loading: _Loading
    dumping: _Dumping


class DictSchema(Generic[T]):

    def __init__(self, cls: Type[T], *,
                 serializers: Iterable[Type[FieldSerializer]] = field_serializers(),
                 allow_missing: bool = _Loading.allow_missing,
                 allow_unexpected: bool = _Loading.allow_unexpected):
        self.descriptor = self._describe(cls)
        self.config = _Config(
            loading=_Loading(allow_missing=allow_missing, allow_unexpected=allow_unexpected),
            dumping=_Dumping()
        )
        self._serializer = SeriousSchema(
            self.descriptor,
            serializers,
            self.config.loading.allow_missing,
            self.config.loading.allow_unexpected
        )

    @staticmethod
    def _describe(cls: Type[T]) -> TypeDescriptor[T]:
        descriptor = describe(cls)
        _check_is_dataclass(descriptor.cls, 'Serious can only operate on dataclasses.')
        return descriptor

    @property
    def cls(self):
        return self.descriptor.cls

    def load(self, data: Dict[str, Any]) -> T:
        return self._from_dict(data)

    def load_many(self, items: Iterable[Dict[str, Any]]) -> List[T]:
        return [self._from_dict(each) for each in items]

    def dump(self, o: T) -> Dict[str, Any]:
        _check_is_instance(o, self.cls)
        return self._serializer.dump(o)

    def dump_many(self, items: Collection[T]) -> List[Dict[str, Any]]:
        return [self._dump(o) for o in items]

    def _dump(self, o) -> Dict[str, Any]:
        return self._serializer.dump(_check_is_instance(o, self.cls))

    def _from_dict(self, data: Mapping):
        return self._serializer.load(data)
