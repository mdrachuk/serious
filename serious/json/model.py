"""A module with `JsonModule` -- Serious model to transform between dataclasses and JSON strings."""
from __future__ import annotations

__all__ = ['JsonModel']

import json
from typing import Optional, TypeVar, Type, Generic, List, MutableMapping, Collection, Iterable, Any, Union

from serious.descriptors import describe
from serious.serialization import FieldSerializer, SeriousModel, field_serializers, KeyMapper
from serious.utils import class_path
from serious.json.utils import camel_to_snake, snake_to_camel
from .checks import check_that_loading_an_object, check_that_loading_a_list

T = TypeVar('T')


class JsonModel(Generic[T]):
    """A model converting dataclasses to JSON strings and back.


        :Example:

        from uuid import UUID
        from dataclasses import dataclass
        from serious import DictModel

        @dataclass
        class Robot:
            serial: UUID
            name: str

        >>> model = JsonModel(Robot)
        >>> model.load('{"serial": "f3179d05-30f6-43ba-b6cb-7556af09330b", "name": "Caliban"}')
        Robot(serial=UUID('f3179d05-30f6-43ba-b6cb-7556af09330b'), name='Caliban')
        >>> model.dump(Robot(UUID('00000000-0000-4000-0000-000002716057'), 'Bender'))
        '{"serial": "00000000-0000-4000-0000-000002716057", "name": "Bender"}'

    Check `__init__` parameters for a list of configuration options.

    `More on models in docs <https://serious.readthedocs.io/en/latest/models/>`_.
    """

    def __init__(
            self,
            cls: Type[T],
            serializers: Iterable[Type[FieldSerializer]] = field_serializers(),
            *,
            allow_any: bool = False,
            allow_missing: bool = False,
            allow_unexpected: bool = False,
            validate_on_load: bool = True,
            validate_on_dump: bool = False,
            ensure_frozen: Union[bool, Iterable[Type]] = False,
            camel_case: bool = True,
            indent: Optional[int] = None,
    ):
        """Initialize a JSON model.

        :param cls: the dataclass type to load/dump.
        :param serializers: field serializer classes in an order they will be tested for fitness for each field.
        :param allow_any: `False` to raise if the model contains fields annotated with `Any`
                (this includes generics like `List[Any]`, or simply `list`).
        :param allow_missing: `False` to raise during load if data is missing the optional fields.
        :param allow_unexpected: `False` to raise during load if data contains some unknown fields.
        :param validate_on_load: to call dataclass `__validate__` method after object construction.
        :param validate_on_load: to call object `__validate__` before dumping.
        :param ensure_frozen: `False` to skip check of model immutability; `True` will perform the check
                against built-in immutable types; a list of custom immutable types is added to built-ins.
        :param camel_case: `True` to transform dataclass "snake_case" to JSON "camelCase".
        :param indent: number of spaces JSON output will be indented by; `None` for most compact representation.
        """
        self.cls = cls
        self.descriptor = describe(cls)
        self.serious_model: SeriousModel = SeriousModel(
            self.descriptor,
            serializers,
            allow_any=allow_any,
            allow_missing=allow_missing,
            allow_unexpected=allow_unexpected,
            validate_on_load=validate_on_load,
            validate_on_dump=validate_on_dump,
            ensure_frozen=ensure_frozen,
            key_mapper=JsonKeyMapper() if camel_case else None,
        )
        self._dump_indentation = indent

    def load(self, json_: str) -> T:
        """Load a dataclass from a JSON string."""
        data: MutableMapping = self._load_from_str(json_)
        check_that_loading_an_object(data, self.cls)
        return self.serious_model.load(data)

    def load_many(self, json_: str) -> List[T]:
        """Load a list of dataclasses from a JSON string."""
        data: Collection = self._load_from_str(json_)
        check_that_loading_a_list(data, self.cls)
        return [self.serious_model.load(each) for each in data]

    def dump(self, o: T) -> str:
        """Dump a single dataclass to a JSON string."""
        as_dict = self.serious_model.dump(o)
        return self._dump_to_str(as_dict)

    def dump_many(self, items: Collection[T]) -> str:
        """Dump a list of dataclasses to a JSON string."""
        as_dicts = [self.serious_model.dump(o) for o in items]
        return self._dump_to_str(as_dicts)

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
        if path == 'serious.json.model.JsonModel':
            path = 'serious.JsonModel'
        return f'<{path}[{class_path(self.cls)}] at {hex(id(self))}>'


class JsonKeyMapper(KeyMapper):

    def to_model(self, key: str) -> str:
        return camel_to_snake(key)

    def to_serialized(self, field: str) -> str:
        return snake_to_camel(field)
