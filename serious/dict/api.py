from __future__ import annotations

from typing import TypeVar, Type, Generic, List, Collection, Dict, Iterable, Any, Mapping

from serious.descriptors import describe, TypeDescriptor
from serious.field_serializers import FieldSerializer, field_serializers
from serious.preconditions import _check_is_instance, _check_is_dataclass
from serious.schema import SeriousSchema
from serious.utils import class_path

T = TypeVar('T')


class DictSchema(Generic[T]):

    def __init__(
            self,
            cls: Type[T],
            *,
            serializers: Iterable[Type[FieldSerializer]] = field_serializers(),
            allow_any: bool = False,
            allow_missing: bool = False,
            allow_unexpected: bool = False,
    ):
        """
        @param cls the descriptor of the dataclass to load/dump.
        @param serializers field serializer classes in an order they will be tested for fitness for each field.
        @param allow_any False to raise if the model contains fields annotated with Any
                (this includes generics like List[Any], or simply list).
        @param allow_missing False to raise during load if data is missing the optional fields.
        @param allow_unexpected False to raise during load if data is missing the contains some unknown fields.
        """
        self.descriptor = self._describe(cls)
        self._serializer = SeriousSchema(
            self.descriptor,
            serializers,
            allow_any=allow_any,
            allow_missing=allow_missing,
            allow_unexpected=allow_unexpected
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

    def __repr__(self):
        path = class_path(type(self))
        if path == 'serious.dict.api.DictSchema':
            path = 'serious.DictSchema'
        return f'<{path}[{class_path(self.cls)}] at {hex(id(self))}>'
