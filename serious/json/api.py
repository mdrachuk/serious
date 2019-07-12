from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Optional, TypeVar, Type, Generic, List, MutableMapping, Collection, Iterable, Any, Dict

from serious.descriptors import describe, TypeDescriptor
from serious.field_serializers import FieldSerializer, field_serializers
from serious.json.preconditions import _check_that_loading_an_object, _check_that_loading_a_list
from serious.preconditions import _check_is_instance, _check_is_dataclass
from serious.schema import SeriousSchema

T = TypeVar('T')


@dataclass(frozen=True)
class _Loading:
    allow_missing: bool = False
    allow_unexpected: bool = False


@dataclass(frozen=True)
class _Dumping:
    indent: Optional[int] = None


@dataclass(frozen=True)
class _Config:
    loading: _Loading
    dumping: _Dumping


class JsonSchema(Generic[T]):

    def __init__(self, cls: Type[T], *,
                 serializers: Iterable[Type[FieldSerializer]] = field_serializers(),
                 allow_missing: bool = _Loading.allow_missing,
                 allow_unexpected: bool = _Loading.allow_unexpected,
                 indent: Optional[int] = _Dumping.indent):
        self.descriptor = self._describe(cls)
        self.config = _Config(
            loading=_Loading(allow_missing=allow_missing, allow_unexpected=allow_unexpected),
            dumping=_Dumping(indent=indent)
        )
        self._serializer = SeriousSchema(
            self.descriptor,
            serializers,
            self.config.loading.allow_missing,
            self.config.loading.allow_unexpected
        )

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
                          indent=self.config.dumping.indent,
                          separators=None,
                          default=None,
                          sort_keys=False)
