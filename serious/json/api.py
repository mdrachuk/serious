from __future__ import annotations

import json
from typing import Optional, TypeVar, Type, Generic, List, MutableMapping, Collection, Iterable, Any, Dict

from serious.descriptors import describe, TypeDescriptor
from serious.field_serializers import FieldSerializer, field_serializers
from serious.json.preconditions import _check_that_loading_an_object, _check_that_loading_a_list
from serious.preconditions import _check_is_instance, _check_is_dataclass
from serious.schema import SeriousSchema
from serious.utils import class_path

T = TypeVar('T')


class JsonSchema(Generic[T]):

    def __init__(
            self,
            cls: Type[T],
            *,
            serializers: Iterable[Type[FieldSerializer]] = field_serializers(),
            allow_any: bool = False,
            allow_missing: bool = False,
            allow_unexpected: bool = False,
            indent: Optional[int] = None,
    ):
        """
        @param cls the descriptor of the dataclass to load/dump.
        @param serializers field serializer classes in an order they will be tested for fitness for each field.
        @param allow_any False to raise if the model contains fields annotated with Any
                (this includes generics like List[Any], or simply list).
        @param allow_missing False to raise during load if data is missing the optional fields.
        @param allow_unexpected False to raise during load if data is missing the contains some unknown fields.
        @param indent number of spaces JSON output will be indented by; `None` for most compact representation.
        """
        self.descriptor = self._describe(cls)
        self._serializer = SeriousSchema(
            self.descriptor,
            serializers,
            allow_any=allow_any,
            allow_missing=allow_missing,
            allow_unexpected=allow_unexpected,
        )
        self._dump_indentation = indent

    @property
    def cls(self):
        return self.descriptor.cls

    @staticmethod
    def _describe(cls: Type[T]) -> TypeDescriptor[T]:
        descriptor = describe(cls)
        _check_is_dataclass(descriptor.cls, 'Serious can only operate on dataclasses.')
        return descriptor

    def load(self, json_: str) -> T:
        data: MutableMapping = self._load_from_str(json_)
        _check_that_loading_an_object(data, self.cls)
        return self._from_dict(data)

    def load_many(self, json_: str) -> List[T]:
        data: Collection = self._load_from_str(json_)
        _check_that_loading_a_list(data, self.cls)
        return [self._from_dict(each) for each in data]

    def dump(self, o: T) -> str:
        _check_is_instance(o, self.cls)
        return self._dump_to_str(self._serializer.dump(o))

    def dump_many(self, items: Collection[T]) -> str:
        dict_items = list(map(self._dump, items))
        return self._dump_to_str(dict_items)

    def _dump(self, o) -> Dict[str, Any]:
        return self._serializer.dump(_check_is_instance(o, self.cls))

    def _from_dict(self, data: MutableMapping) -> T:
        return self._serializer.load(data)

    def _load_from_str(self, json_: str) -> Any:
        """Override to customize JSON loading behaviour."""
        return json.loads(json_)

    def _dump_to_str(self, dict_items: Any) -> str:
        """Override to customize JSON dumping behaviour."""
        return json.dumps(dict_items,
                          skipkeys=False,
                          ensure_ascii=False,
                          check_circular=True,
                          allow_nan=False,
                          indent=self._dump_indentation,
                          separators=None,
                          default=None,
                          sort_keys=False)

    def __repr__(self):
        path = class_path(type(self))
        if path == 'serious.json.api.JsonSchema':
            path = 'serious.JsonSchema'
        return f'<{path}[{class_path(self.cls)}] at {hex(id(self))}>'
