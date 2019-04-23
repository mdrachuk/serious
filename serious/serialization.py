from dataclasses import (fields, is_dataclass, dataclass, Field, MISSING, replace)
from datetime import datetime, timezone
from enum import Enum
from typing import (Mapping, Union, Type, Any, Dict, Iterator, NamedTuple, Callable,
                    get_type_hints, Generic, TypeVar, List, _GenericAlias, Collection)
from uuid import UUID

from serious.utils import (_is_collection, _is_mapping, _is_optional)

serious = 'serious'

DataClass = Any
JSON = Union[Mapping, List, str, int, float, bool, None]


class FieldSerializer(NamedTuple):
    dump: Callable[[Any], JSON]
    load: Callable[[JSON], Any]


noop_serializer = FieldSerializer(load=lambda o: o, dump=lambda o: o)
uuid_serializer = FieldSerializer(load=UUID, dump=lambda o: str(o))
datetime_timestamp_serializer = FieldSerializer(
    load=lambda o: datetime.fromtimestamp(o, datetime.now(timezone.utc).astimezone().tzinfo),
    dump=lambda o: o.timestamp()
)


@dataclass(frozen=True)
class _Attr:
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


def _attrs(cls: Type[DataClass]) -> Iterator[_Attr]:
    types = get_type_hints(cls)
    return (_Attr(cls, f.name, types[f.name], f.metadata) for f in fields(cls))


def _fields_missing_from(data: Mapping, cls: Type[DataClass]) -> Iterator[Field]:
    def _is_missing(field: Field) -> bool:
        return field.name not in data and field.default is MISSING and field.default_factory is MISSING

    return filter(_is_missing, fields(cls))


T = TypeVar('T')


class DataClassPlainDictSerializer(Generic[T]):
    def __init__(self, cls: Type[T], allow_missing, allow_unexpected, _registry=None):
        self._cls = cls
        self._allow_missing = allow_missing
        self._allow_unexpected = allow_unexpected
        self._serializer_registry = {cls: self} if _registry is None else _registry
        self._field_serializers = self._field_serializers(cls)

    def _child_serializer(self, cls: Type[DataClass]):
        if cls in self._serializer_registry:
            return self._serializer_registry[cls]
        new_serializer = DataClassPlainDictSerializer(cls, self._allow_missing, self._allow_unexpected)
        self._serializer_registry[cls] = new_serializer
        return new_serializer

    def load(self, data: Mapping) -> T:
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
        init_kwargs = {
            key: serializer.load(mut_data[key])
            for key, serializer in self._field_serializers.items()
            if key in mut_data
        }
        return self._cls(**init_kwargs)

    def dump(self, o: T) -> Dict[str, Any]:
        return {key: serializer.dump(getattr(o, key)) for key, serializer in self._field_serializers.items()}

    def _field_serializers(self, cls: Type[DataClass]) -> Dict[str, FieldSerializer]:
        return {attr.name: self._field_serializer(attr) for attr in _attrs(cls)}

    def _field_serializer(self, attr):
        if attr.contains_serious_metadata:
            return FieldSerializer(load=attr.serious_metadata['load'], dump=attr.serious_metadata['dump'])
        if isinstance(attr.type, _GenericAlias):
            if _is_optional(attr.type):
                present_s = self._field_serializer(replace(attr, type=attr.type.__args__[0]))
                return FieldSerializer(
                    load=lambda x: None if x is None else present_s.load(x),
                    dump=lambda x: None if x is None else present_s.dump(x)
                )
            elif _is_collection(attr.type):
                if _is_mapping(attr.type):
                    key_s = self._field_serializer(replace(attr, type=attr.type.__args__[0]))
                    item_s = self._field_serializer(replace(attr, type=attr.type.__args__[1]))
                    return FieldSerializer(
                        load=lambda d: attr.type.__origin__(
                            {key_s.load(key): item_s.load(value) for key, value in d.items()}),
                        dump=lambda d: {key_s.dump(key): item_s.dump(value) for key, value in d.items()}
                    )
                else:  # is list/set/tuple/etc
                    item_s = self._field_serializer(replace(attr, type=attr.type.__args__[0]))
                    return FieldSerializer(
                        load=lambda items: attr.type.__origin__([item_s.load(item) for item in items]),
                        dump=lambda items: [item_s.dump(item) for item in items]
                    )
        elif issubclass(attr.type, (str, int, float, bool)):
            return FieldSerializer(load=attr.type, dump=attr.type)
        elif is_dataclass(attr.type):
            dataclass_s = self._child_serializer(attr.type)
            return FieldSerializer(load=dataclass_s.load, dump=dataclass_s.dump)
        elif issubclass(attr.type, datetime):
            return datetime_timestamp_serializer
        elif issubclass(attr.type, UUID):
            return uuid_serializer
        elif issubclass(attr.type, Enum):
            return FieldSerializer(load=attr.type, dump=lambda o: o.value)
        raise Exception(f'{attr.type} is unsupported')


def _check_for_missing(cls: Type[DataClass], data: Mapping) -> None:
    missing_fields = _fields_missing_from(data, cls)
    first_missing_field = next(missing_fields, MISSING)
    if first_missing_field is not MISSING:
        field_names = {first_missing_field.name} | {field.name for field in missing_fields}
        raise MissingField(field_names, cls)


def _check_for_unexpected(cls: Type[DataClass], data: Mapping) -> None:
    field_names = {field.name for field in fields(cls)}
    data_keys = set(data.keys())
    unexpected_fields = data_keys - field_names
    if any(unexpected_fields):
        raise UnexpectedItem(unexpected_fields, cls)


class UnexpectedItem(Exception):
    def __init__(self, fields: Collection[str], cls: Type[DataClass]):
        if len(fields) == 1:
            field = next(iter(fields))
            message = f'Unexpected field "{field}" in loaded {_class_path(cls)}'
        else:
            message = f'Unexpected fields {fields} in loaded {_class_path(cls)}'
        super().__init__(message)


class MissingField(Exception):
    def __init__(self, fields: Collection[str], cls: Type[DataClass]):
        if len(fields) == 1:
            field = next(iter(fields))
            message = f'Missing field "{field}" in loaded {_class_path(cls)}'
        else:
            message = f'Missing fields {fields} in loaded {_class_path(cls)}'
        super().__init__(message)


def _class_path(cls):
    return f'{cls.__module__}.{cls.__qualname__}'
