from __future__ import annotations

from dataclasses import fields, Field, MISSING
from typing import Mapping, Type, Any, Dict, Iterator, Generic, TypeVar, List

from serious.attr import Attr
from serious.context import SerializationContext
from serious.errors import LoadError, DumpError, UnexpectedItem, MissingField
from serious.serializer_options import SerializerOption
from serious.field_serializers import FieldSerializer
from serious.utils import DataClass

T = TypeVar('T')


class SeriousSerializer(Generic[T]):
    def __init__(self,
                 cls: Type[T],
                 allow_missing: bool,
                 allow_unexpected: bool,
                 serializers: List[SerializerOption] = None,
                 _registry: Dict[Type[DataClass], SeriousSerializer] = None):
        self._cls = cls
        self._serializers = tuple(serializers or SerializerOption.defaults())
        self._allow_missing = allow_missing
        self._allow_unexpected = allow_unexpected
        self._serializer_registry = {cls: self} if _registry is None else _registry
        self._field_serializers = self._build_field_serializers(cls)

    def child_serializer(self, cls: Type[DataClass]) -> SeriousSerializer:
        if cls in self._serializer_registry:
            return self._serializer_registry[cls]
        new_serializer = SeriousSerializer(cls, self._allow_missing, self._allow_unexpected)
        self._serializer_registry[cls] = new_serializer
        return new_serializer

    def load(self, data: Mapping, _ctx: SerializationContext = None) -> T:
        _ctx = _ctx or SerializationContext()
        if not isinstance(data, Mapping):
            raise Exception(f'Invalid data for {self._cls}')
        mut_data = dict(data)
        if self._allow_missing:
            for field in _fields_missing_from(mut_data, self._cls):
                mut_data[field.name] = None
        else:
            _check_for_missing(self._cls, mut_data)
        if not self._allow_unexpected:
            _check_for_unexpected(self._cls, mut_data)
        try:
            init_kwargs = {
                key: serializer.load(mut_data[key], _ctx.root)
                for key, serializer in self._field_serializers.items()
                if key in mut_data
            }
        except Exception as e:
            if not _ctx.is_root:
                raise
            raise LoadError(self._cls, _ctx.stack, data) from e
        result = self._cls(**init_kwargs)  # type: ignore # not an object
        return result

    def dump(self, o: T, ctx: SerializationContext = None) -> Dict[str, Any]:
        ctx = ctx or SerializationContext()
        try:
            result = {
                key: serializer.dump(getattr(o, key), ctx.root)
                for key, serializer in self._field_serializers.items()
            }
        except Exception as e:
            if not ctx.is_root:
                raise
            raise DumpError(o, ctx.stack) from e
        return result

    def _build_field_serializers(self, cls: Type[DataClass]) -> Dict[str, FieldSerializer]:
        return {attr.name: self.field_serializer(attr) for attr in Attr.list(cls)}

    def field_serializer(self, attr, track=True) -> FieldSerializer:
        serializer = self._untracked_field_serializer(attr)
        if track:
            serializer = serializer.with_stack()
        return serializer

    def _untracked_field_serializer(self, attr: Attr) -> FieldSerializer:
        options = (option.factory(attr, self) for option in self._serializers if option.fits(attr))
        serializer = next(options, None)
        if serializer is None:
            raise Exception(f'{attr.type} is unsupported')
        return serializer


def _check_for_missing(cls: Type[DataClass], data: Mapping) -> None:
    missing_fields = _fields_missing_from(data, cls)
    first_missing_field: Any = next(missing_fields, MISSING)
    if first_missing_field is not MISSING:
        field_names = {first_missing_field.name} | {field.name for field in missing_fields}
        raise MissingField(field_names, cls)


def _check_for_unexpected(cls: Type[DataClass], data: Mapping) -> None:
    field_names = {field.name for field in fields(cls)}
    data_keys = set(data.keys())
    unexpected_fields = data_keys - field_names
    if any(unexpected_fields):
        raise UnexpectedItem(unexpected_fields, cls)


def _fields_missing_from(data: Mapping, cls: Type[DataClass]) -> Iterator[Field]:
    def _is_missing(field: Field) -> bool:
        return field.name not in data \
               and field.default is MISSING \
               and field.default_factory is MISSING  # type: ignore # default factory is an unbound function

    return filter(_is_missing, fields(cls))
