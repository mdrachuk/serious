"""A module with `DictModel` -- Serious model to transform between dataclasses and dictionaries."""
from __future__ import annotations

__all__ = ['DictModel']

from typing import TypeVar, Type, Generic, List, Collection, Dict, Iterable, Any, Union

from serious.descriptors import describe, TypeDescriptor
from serious.serialization import FieldSerializer, SeriousModel, field_serializers
from serious.utils import class_path

T = TypeVar('T')


class DictModel(Generic[T]):
    """A model converting dataclasses to dicts and back.


        :Example:

        from uuid import UUID
        from dataclasses import dataclass
        from serious import DictModel

        @dataclass
        class Robot:
            serial: UUID
            name: str

        >>> model = DictModel(Robot)
        >>> model.load({'serial': 'f3179d05-30f6-43ba-b6cb-7556af09330b', 'name': 'Caliban'})
        Robot(serial=UUID('f3179d05-30f6-43ba-b6cb-7556af09330b'), name='Caliban')
        >>> model.dump(Robot(UUID('00000000-0000-4000-0000-000002716057'), 'Bender'))
        {'serial': '00000000-0000-4000-0000-000002716057', 'name': 'Bender'}

    Check `__init__` parameters for a list of configuration options.

    `More on models in docs <https://serious.readthedocs.io/en/latest/models/>`_.
    """
    descriptor: TypeDescriptor
    serious_model: SeriousModel

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
    ):
        """Initialize a dictionary model.

        :param cls: the dataclass type to load/dump.
        :param serializers: field serializer classes in an order they will be tested for fitness for each field.
        :param allow_any: `False` to raise if the model contains fields annotated with `Any`
                (this includes generics like `List[Any]`, or simply `list`).
        :param allow_missing: `False` to raise during load if data is missing the optional fields.
        :param allow_unexpected: `False` to raise during load if data contains some unknown fields.
        :param validate_on_load: to call dataclass `__validate__` method after object construction.
        :param validate_on_dump: to call object `__validate__` before dumping.
        :param ensure_frozen: `False` to skip check of model immutability; `True` will perform the check
                against built-in immutable types; a list of custom immutable types is added to built-ins.
        """
        self.cls = cls
        self.descriptor = describe(cls)
        self.serious_model = SeriousModel(
            self.descriptor,
            serializers,
            allow_any=allow_any,
            allow_missing=allow_missing,
            allow_unexpected=allow_unexpected,
            validate_on_load=validate_on_load,
            validate_on_dump=validate_on_dump,
            ensure_frozen=ensure_frozen,
        )

    def load(self, data: Dict[str, Any]) -> T:
        """Load dataclass from a dictionary."""
        return self.serious_model.load(data)

    def load_many(self, items: Iterable[Dict[str, Any]]) -> List[T]:
        """Load a list of dataclasses from a dictionary."""
        return [self.load(each) for each in items]

    def dump(self, o: T) -> Dict[str, Any]:
        """Dump a dataclasses to a dictionary."""
        return self.serious_model.dump(o)

    def dump_many(self, items: Collection[T]) -> List[Dict[str, Any]]:
        """Dump a list dataclasses to a dictionary."""
        return [self.dump(o) for o in items]

    def __repr__(self):
        path = class_path(type(self))
        if path == 'serious.dict.model.DictModel':
            path = 'serious.DictModel'
        return f'<{path}[{class_path(self.cls)}] at {hex(id(self))}>'
