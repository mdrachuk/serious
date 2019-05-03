from __future__ import annotations

from dataclasses import fields, Field, MISSING
from typing import Mapping, Type, Any, Dict, Iterator, Generic, TypeVar, Optional, Iterable

from serious.attr import Attr
from serious.context import SerializationContext
from serious.errors import LoadError, DumpError, UnexpectedItem, MissingField
from serious.field_serializers import FieldSerializer
from serious.preconditions import _check_present, _check_is_instance
from serious.serializer_options import SerializerOption
from serious.utils import DataClass

T = TypeVar('T')


class SeriousSerializer(Generic[T]):
    def __init__(
            self,
            cls: Type[T],
            serializers: Iterable[SerializerOption],
            allow_missing: bool,
            allow_unexpected: bool,
            _registry: Dict[Type[DataClass], SeriousSerializer] = None
    ):
        self._cls = cls
        self._serializers = tuple(serializers)
        self._allow_missing = allow_missing
        self._allow_unexpected = allow_unexpected
        self._serializer_registry = {cls: self} if _registry is None else _registry
        self._field_serializers = self._build_field_serializers(cls)

    def child_serializer(self, cls: Type[DataClass]) -> SeriousSerializer:
        if cls in self._serializer_registry:
            return self._serializer_registry[cls]
        new_serializer = SeriousSerializer(cls, self._serializers, self._allow_missing, self._allow_unexpected)
        self._serializer_registry[cls] = new_serializer
        return new_serializer

    def load(self, data: Mapping, _ctx: Optional[SerializationContext] = None) -> T:
        _check_is_instance(data, Mapping, f'Invalid data for {self._cls}')  # type: ignore
        root = _ctx is None
        ctx: SerializationContext = SerializationContext() if root else _ctx  # type: ignore # checked above
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
                key: serializer.load(mut_data[key], ctx)
                for key, serializer in self._field_serializers.items()
                if key in mut_data
            }
        except Exception as e:
            if root:
                raise LoadError(self._cls, ctx.stack, data) from e
            raise
        return self._cls(**init_kwargs)  # type: ignore # not an object

    def dump(self, o: T, _ctx: Optional[SerializationContext] = None) -> Dict[str, Any]:
        _check_is_instance(o, self._cls)
        root = _ctx is None
        ctx: SerializationContext = SerializationContext() if root else _ctx  # type: ignore # checked above
        try:
            return {
                key: serializer.dump(getattr(o, key), ctx)
                for key, serializer in self._field_serializers.items()
            }
        except Exception as e:
            if root:
                raise DumpError(o, ctx.stack) from e
            raise

    def _build_field_serializers(self, cls: Type[DataClass]) -> Dict[str, FieldSerializer]:
        return {attr.name: self.field_serializer(attr) for attr in Attr.list(cls)}

    def field_serializer(self, attr: Attr, tracked: bool = True) -> FieldSerializer:
        optional = self._get_serializer(attr)
        serializer = _check_present(optional, f'Type "{attr.type}" is not supported')
        return serializer.with_stack() if tracked else serializer

    def _get_serializer(self, attr: Attr) -> Optional[FieldSerializer]:
        options = (option.factory(attr, self) for option in self._serializers if option.fits(attr))  # type: ignore
        optional = next(options, None)
        return optional


def _check_for_missing(cls: Type[DataClass], data: Mapping) -> None:
    missing_fields = filter(lambda f: f.name not in data, fields(cls))
    first_missing_field: Any = next(missing_fields, MISSING)
    if first_missing_field is not MISSING:
        field_names = {first_missing_field.name} | {field.name for field in missing_fields}
        raise MissingField(cls, data, field_names)


def _check_for_unexpected(cls: Type[DataClass], data: Mapping) -> None:
    field_names = {field.name for field in fields(cls)}
    data_keys = set(data.keys())
    unexpected_fields = data_keys - field_names
    if any(unexpected_fields):
        raise UnexpectedItem(cls, data, unexpected_fields)


def _fields_missing_from(data: Mapping, cls: Type[DataClass]) -> Iterator[Field]:
    def _is_missing(field: Field) -> bool:
        return field.name not in data \
               and field.default is MISSING \
               and field.default_factory is MISSING  # type: ignore # default factory is an unbound function

    return filter(_is_missing, fields(cls))
