from __future__ import annotations

import abc
import copy
from contextlib import contextmanager
from dataclasses import (fields, is_dataclass, dataclass, Field, MISSING, replace)
from datetime import datetime, timezone
from enum import Enum
from typing import (Mapping, Type, Any, Dict, Iterator, Callable,  # type: ignore # _GenericAlias exists!
                    get_type_hints, Generic, TypeVar, _GenericAlias, List, Tuple)
from uuid import UUID

from serious.errors import LoadError, DumpError, UnexpectedItem, MissingField
from serious.utils import (_is_collection, _is_mapping, _is_optional, DataClass, Primitive)

local_tz = datetime.now(timezone.utc).astimezone().tzinfo

serious = 'serious'

DumpF = Callable[[Any], Primitive]
LoadF = Callable[[Primitive], Any]


class _SerializationContext:
    def __init__(self, _root: _SerializationContext = None):
        self._stack: List[str] = list()
        self._root: _SerializationContext = _root or self

    @contextmanager
    def enter(self, name: str):
        self._stack.append(name)
        yield
        self._stack.pop()

    @property
    def is_root(self) -> bool:
        return self._root is self

    @property
    def root(self) -> _SerializationContext:
        return self._root

    @property
    def stack(self) -> Tuple[str, ...]:
        return tuple(self.stack)


class FieldSerializer(abc.ABC):
    def __init__(self, attr: Attr):
        self._attr = attr

    def with_stack(self):
        entry = f'.{self.attr.name}'
        serializer = copy.copy(self)
        setattr(serializer, 'load', with_stack(self.load, entry))
        setattr(serializer, 'dump', with_stack(self.dump, entry))
        return serializer

    @property
    def attr(self):
        return self._attr

    @abc.abstractmethod
    def dump(self, value: Any, ctx: _SerializationContext) -> Primitive:
        pass

    @abc.abstractmethod
    def load(self, value: Primitive, ctx: _SerializationContext) -> Any:
        pass


def with_stack(f: Callable, entry: str = None, entry_factory: Callable = None):
    if (not entry and not entry_factory) or (entry and entry_factory):
        raise Exception('Only one of entry and entry_factory is expected')

    def _wrap(*args):
        ctx: _SerializationContext = args[-1]
        with ctx.enter(entry or entry_factory()):
            return f(*args)

    return _wrap


class DirectFieldSerializer(FieldSerializer):
    def __init__(self, attr: Attr, load: LoadF, dump: DumpF):
        super().__init__(attr)
        self._load = load
        self._dump = dump

    def load(self, value: Primitive, ctx: _SerializationContext) -> Any:
        return self._load(value)

    def dump(self, value: Any, ctx: _SerializationContext) -> Primitive:
        return self._dump(value)


class CollectionFieldSerializer(FieldSerializer):
    def __init__(self, attr: Attr, item_serializer: FieldSerializer):
        super().__init__(attr)
        self._load_item = item_serializer.load
        self._dump_item = item_serializer.dump

    def with_stack(self):
        serializer = super().with_stack()

        item_entry = lambda i, *_: f'[{i}]'
        setattr(serializer, 'load_item', with_stack(self.load_item, entry_factory=item_entry))
        setattr(serializer, 'dump_item', with_stack(self.dump_item, entry_factory=item_entry))

        return serializer

    def load(self, value: Primitive, ctx: _SerializationContext) -> Any:
        items = [self.load_item(i, item, ctx) for i, item in enumerate(value)]  # type: ignore # value is a collection
        return self._attr.type.__origin__(items)

    def dump(self, value: Any, ctx: _SerializationContext) -> Primitive:
        return [self.dump_item(i, item, ctx) for i, item in enumerate(value)]

    def load_item(self, i: int, value: Primitive, ctx: _SerializationContext):
        return self._load_item(value, ctx)

    def dump_item(self, i: int, value: Any, ctx: _SerializationContext):
        return self._dump_item(value, ctx)


class DataclassFieldSerializer(FieldSerializer):
    def __init__(self, attr: Attr, serializer: PrimitiveSerializer):
        super().__init__(attr)
        self._serializer = serializer

    def load(self, value: Primitive, ctx: _SerializationContext) -> Any:
        return self._serializer.load(value, ctx)  # type: ignore # type: ignore # value always a mapping

    def dump(self, value: Any, ctx: _SerializationContext) -> Primitive:
        return self._serializer.dump(value, ctx)


class DictFieldSerializer(FieldSerializer):
    def __init__(self, attr: Attr, key_serializer: FieldSerializer, value_serializer: FieldSerializer):
        super().__init__(attr)
        self._dump_key = key_serializer.dump
        self._load_key = key_serializer.load
        self._dump_value = value_serializer.dump
        self._load_value = value_serializer.load

    def with_stack(self):
        serializer = super().with_stack()

        value_entry = lambda key, *_: f'[{key}]'
        setattr(serializer, 'dump_value', with_stack(self.dump_value, entry_factory=value_entry))
        setattr(serializer, 'load_value', with_stack(self.load_value, entry_factory=value_entry))

        key_entry = lambda key, *_: f'${key}'
        setattr(serializer, 'dump_key', with_stack(self.dump_key, entry_factory=key_entry))
        setattr(serializer, 'load_key', with_stack(self.load_key, entry_factory=key_entry))

        return serializer

    def load(self, data: Primitive, ctx: _SerializationContext) -> Any:
        items = {
            self.load_key(key, ctx): self.load_value(key, value, ctx)
            for key, value in data.items()  # type: ignore # data is always a dict
        }
        return self.attr.type.__origin__(items)

    def dump(self, d: Any, ctx: _SerializationContext) -> Primitive:
        return {self.dump_key(key, ctx): self.dump_value(key, value, ctx) for key, value in d.items()}

    def load_value(self, key: str, value: Primitive, ctx: _SerializationContext) -> Any:
        return self._load_value(value, ctx)

    def dump_value(self, key: str, value: Any, ctx: _SerializationContext) -> Primitive:
        return self._dump_value(value, ctx)

    def load_key(self, key: str, ctx: _SerializationContext) -> Any:
        return self._load_key(key, ctx)

    def dump_key(self, key: Any, ctx: _SerializationContext) -> str:
        return str(self._dump_key(key, ctx))


class OptionalFieldSerializer(FieldSerializer):
    def __init__(self, attr: Attr, serializer: FieldSerializer):
        super().__init__(attr)
        self._serializer = serializer

    def dump(self, value: Any, ctx: _SerializationContext) -> Primitive:
        return None if value is None else self._serializer.dump(value, ctx)

    def load(self, value: Primitive, ctx: _SerializationContext) -> Any:
        return None if value is None else self._serializer.load(value, ctx)


@dataclass(frozen=True)
class Attr:
    of: Type[DataClass]
    name: str
    type: Type
    metadata: Any

    @property
    def contains_serious_metadata(self):
        return self.metadata is not None and serious in self.metadata

    @property
    def serious_metadata(self):
        return self.metadata[serious]


def _attrs(cls: Type[DataClass]) -> Iterator[Attr]:
    types = get_type_hints(cls)
    return (Attr(cls, f.name, types[f.name], f.metadata) for f in fields(cls))


def _fields_missing_from(data: Mapping, cls: Type[DataClass]) -> Iterator[Field]:
    def _is_missing(field: Field) -> bool:
        return field.name not in data \
               and field.default is MISSING \
               and field.default_factory is MISSING  # type: ignore # default factory is an unbound function

    return filter(_is_missing, fields(cls))


T = TypeVar('T')


class PrimitiveSerializer(Generic[T]):
    def __init__(self,
                 cls: Type[T],
                 allow_missing: bool,
                 allow_unexpected: bool,
                 _registry: Dict[Type[DataClass], PrimitiveSerializer] = None):
        self._cls = cls
        self._allow_missing = allow_missing
        self._allow_unexpected = allow_unexpected
        self._serializer_registry = {cls: self} if _registry is None else _registry
        self._field_serializers = self._build_field_serializers(cls)

    def child_serializer(self, cls: Type[DataClass]) -> PrimitiveSerializer:
        if cls in self._serializer_registry:
            return self._serializer_registry[cls]
        new_serializer = PrimitiveSerializer(cls, self._allow_missing, self._allow_unexpected)
        self._serializer_registry[cls] = new_serializer
        return new_serializer

    def load(self, data: Mapping, _ctx: _SerializationContext = None) -> T:
        _ctx = _ctx or _SerializationContext()
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

    def dump(self, o: T, ctx: _SerializationContext = None) -> Dict[str, Any]:
        ctx = ctx or _SerializationContext()
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
        return {attr.name: self.field_serializer(attr) for attr in _attrs(cls)}

    def field_serializer(self, attr, track=True) -> FieldSerializer:
        serializer = self._untracked_field_serializer(attr)
        if track:
            serializer = serializer.with_stack()
        return serializer

    def _untracked_field_serializer(self, attr: Attr) -> FieldSerializer:
        options = (option.factory(attr, self) for option in serializer_options if option.fits(attr))
        serializer = next(options, None)
        if serializer is None:
            raise Exception(f'{attr.type} is unsupported')
        return serializer


@dataclass(frozen=True)
class SerializerOption:
    fits: Callable[[Attr], bool]
    factory: Callable[[Attr, PrimitiveSerializer], FieldSerializer]


metadata_serializer = SerializerOption(
    fits=lambda attr: attr.contains_serious_metadata,
    factory=lambda attr, sr: DirectFieldSerializer(attr,
                                                   load=attr.serious_metadata['load'],
                                                   dump=attr.serious_metadata['dump'])
)


def _optional_serializer_factory(attr: Attr, sr: PrimitiveSerializer) -> FieldSerializer:
    present_serializer = sr.field_serializer(replace(attr, type=attr.type.__args__[0]), track=False)
    return OptionalFieldSerializer(attr, present_serializer)


optional_serializer = SerializerOption(
    fits=lambda attr: isinstance(attr.type, _GenericAlias) and _is_optional(attr.type),
    factory=_optional_serializer_factory
)


def _mapping_serializer_factory(attr: Attr, sr: PrimitiveSerializer) -> FieldSerializer:
    key_serializer = sr.field_serializer(replace(attr, type=attr.type.__args__[0]), track=False)
    val_serializer = sr.field_serializer(replace(attr, type=attr.type.__args__[1]), track=False)
    return DictFieldSerializer(attr, key_serializer, val_serializer)


mapping_serializer = SerializerOption(
    fits=lambda attr: isinstance(attr.type, _GenericAlias) and _is_mapping(attr.type),
    factory=_mapping_serializer_factory
)


def _collection_serializer_factory(attr: Attr, sr: PrimitiveSerializer) -> FieldSerializer:
    item_serializer = sr.field_serializer(replace(attr, type=attr.type.__args__[0]), track=False)
    return CollectionFieldSerializer(attr, item_serializer)


collection_serializer = SerializerOption(
    fits=lambda attr: isinstance(attr.type, _GenericAlias) and _is_collection(attr.type),
    factory=_collection_serializer_factory
)

primitive_serializer = SerializerOption(
    fits=lambda attr: issubclass(attr.type, (str, int, float, bool)),
    factory=lambda attr, sr: DirectFieldSerializer(attr, load=attr.type, dump=attr.type)
)


def _dataclass_serializer_factory(attr: Attr, sr: PrimitiveSerializer) -> FieldSerializer:
    dc_serializer = sr.child_serializer(attr.type)
    return DataclassFieldSerializer(attr, dc_serializer)


dataclass_serializer = SerializerOption(
    fits=lambda attr: is_dataclass(attr.type),
    factory=_dataclass_serializer_factory
)

datettime_timestamp_serializer = SerializerOption(
    fits=lambda attr: issubclass(attr.type, datetime),
    factory=lambda attr, sr: DirectFieldSerializer(attr,
                                                   load=lambda o: datetime.fromtimestamp(o, local_tz),
                                                   dump=lambda o: o.timestamp())
)

uuid_serializer = SerializerOption(
    fits=lambda attr: issubclass(attr.type, UUID),
    factory=lambda attr, sr: DirectFieldSerializer(attr, load=UUID, dump=lambda o: str(o))
)

enum_serializer = SerializerOption(
    fits=lambda attr: issubclass(attr.type, Enum),
    factory=lambda attr, sr: DirectFieldSerializer(attr, load=attr.type, dump=lambda o: o.value)
)

serializer_options = [
    metadata_serializer,
    optional_serializer,
    mapping_serializer,
    collection_serializer,
    primitive_serializer,
    dataclass_serializer,
    datettime_timestamp_serializer,
    uuid_serializer,
    enum_serializer
]


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
