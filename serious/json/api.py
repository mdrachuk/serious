from __future__ import annotations

import json
from typing import Optional, TypeVar, Type, Generic, List, MutableMapping, Collection, Iterable, Any, Dict, Union

from serious.descriptors import describe
from serious.preconditions import check_is_instance
from serious.serialization import FieldSerializer, SeriousModel, field_serializers
from serious.serialization.model import KeyMapper
from serious.utils import class_path, snake_to_camel, camel_to_snake
from .preconditions import check_that_loading_an_object, check_that_loading_a_list

T = TypeVar('T')


class JsonModel(Generic[T]):

    def __init__(
            self,
            cls: Type[T],
            serializers: Iterable[Type[FieldSerializer]] = field_serializers(),
            *,
            allow_any: bool = False,
            allow_missing: bool = False,
            allow_unexpected: bool = False,
            ensure_frozen: Union[bool, Iterable[Type]] = False,
            camel_case: bool = True,
            indent: Optional[int] = None,
    ):
        """
        @param cls the dataclass type to load/dump.
        @param serializers field serializer classes in an order they will be tested for fitness for each field.
        @param allow_any `False` to raise if the model contains fields annotated with `Any`
                (this includes generics like `List[Any]`, or simply `list`).
        @param allow_missing `False` to raise during load if data is missing the optional fields.
        @param allow_unexpected `False` to raise during load if data contains some unknown fields.
        @param ensure_frozen `False` to skip check of model immutability; `True` will perform the check
                against built-in immutable types; a list of custom immutable types is added to built-ins.
        @param camel_case `True` to transform dataclass "snake_case" to JSON "camelCase".
        @param indent number of spaces JSON output will be indented by; `None` for most compact representation.
        """
        self._descriptor = describe(cls)
        self._serializer: SeriousModel = SeriousModel(
            self._descriptor,
            serializers,
            allow_any=allow_any,
            allow_missing=allow_missing,
            allow_unexpected=allow_unexpected,
            ensure_frozen=ensure_frozen,
            key_mapper=JsonKeyMapper() if camel_case else None,
        )
        self._dump_indentation = indent

    @property
    def cls(self):
        return self._descriptor.cls

    def load(self, json_: str) -> T:
        data: MutableMapping = self._load_from_str(json_)
        check_that_loading_an_object(data, self.cls)
        return self._from_dict(data)

    def load_many(self, json_: str) -> List[T]:
        data: Collection = self._load_from_str(json_)
        check_that_loading_a_list(data, self.cls)
        return [self._from_dict(each) for each in data]

    def dump(self, o: T) -> str:
        check_is_instance(o, self.cls)
        return self._dump_to_str(self._serializer.dump(o))

    def dump_many(self, items: Collection[T]) -> str:
        dict_items = list(map(self._dump, items))
        return self._dump_to_str(dict_items)

    def _dump(self, o) -> Dict[str, Any]:
        return self._serializer.dump(check_is_instance(o, self.cls))

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
        if path == 'serious.json.api.JsonModel':
            path = 'serious.JsonModel'
        return f'<{path}[{class_path(self.cls)}] at {hex(id(self))}>'


class JsonKeyMapper(KeyMapper):

    def to_model(self, item: str) -> str:
        return camel_to_snake(item)

    def to_serialized(self, item: str) -> str:
        return snake_to_camel(item)
