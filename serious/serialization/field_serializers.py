from __future__ import annotations

__all__ = [
    'field_serializers',
    'OptionalSerializer', 'AnySerializer', 'EnumSerializer', 'DictSerializer', 'CollectionSerializer',
    'TupleSerializer', 'StringSerializer', 'BooleanSerializer', 'IntegerSerializer', 'FloatSerializer',
    'DataclassSerializer', 'UtcTimestampSerializer', 'DateTimeIsoSerializer', 'DateIsoSerializer',
    'TimeIsoSerializer', 'UuidSerializer', 'DecimalSerializer'
]

import re
from dataclasses import replace
from datetime import datetime, date, time
from decimal import Decimal
from enum import Enum
from typing import Any, Optional, Dict, List, Union, Pattern, Iterable, Type, Tuple, Literal, TypeVar
from uuid import UUID

from serious.descriptors import TypeDescriptor
from serious.errors import ValidationError
from serious.types import Timestamp, FrozenList, FrozenDict
from .context import Context, Loading, Dumping
from .serializer import FieldSerializer, Serializer


def field_serializers(custom: Iterable[Type[FieldSerializer]] = tuple()) -> Tuple[Type[FieldSerializer], ...]:
    """Default list of Serious field serializers.

    Returns a frozen collection of field serializers in the default order.
    You can provide a list of custom field serializers to include them along with default serializers.
    The order in the collection defines the order in which the serializers will be tested for fitness for each field.

    :param custom: a list of custom serializers which are injected into the default list

    """
    return tuple([
        OptionalSerializer,
        UnionSerializer,
        AnySerializer,
        LiteralSerializer,
        EnumSerializer,
        *custom,
        TypedDictSerializer,
        DictSerializer,
        CollectionSerializer,
        TupleSerializer,
        StringSerializer,
        BooleanSerializer,
        IntegerSerializer,
        FloatSerializer,
        DataclassSerializer,
        UtcTimestampSerializer,
        DateTimeIsoSerializer,
        DateIsoSerializer,
        TimeIsoSerializer,
        UuidSerializer,
        DecimalSerializer,
    ])


class OptionalSerializer(FieldSerializer[Optional[Any], Optional[Any]]):
    """
    A serializer for field marked as `Optional`. An optional field has internally a serializer for the target type,
    but first checks if the loaded data is `None`.

        :Example:

        @dataclass
        class Node:
            node: Optional[Node]
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        item_descriptor = replace(self.type, is_optional=False)
        self._serializer = self.root.find_serializer(item_descriptor)

    def load(self, value: Optional[Any], ctx: Loading) -> Optional[Any]:
        return None if value is None else self._serializer.load(value, ctx)

    def dump(self, value: Optional[Any], ctx: Dumping) -> Optional[Any]:
        return None if value is None else self._serializer.dump(value, ctx)

    @classmethod
    def fits(cls, desc: TypeDescriptor) -> bool:
        return desc.is_optional


class UnionSerializer(FieldSerializer[Any, Dict]):
    """
    A serializer for Union fields.

        :Example:

        @dataclass
        class Character:
            weapon: Union[Sword, Staff, Hammer]
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._serializers_by_cls = {
            desc.cls: self.root.find_serializer(desc) for desc in self.type.parameters.values()
        }
        self._serializers_by_name = {cls.__name__: serializer for cls, serializer in self._serializers_by_cls.items()}

    def load(self, value: Dict, ctx: Loading) -> Any:
        try:
            value = dict(value)
        except TypeError:
            raise ValidationError(f'Invalid Union[{",".join(self._serializers_by_name)}] value: {value}, '
                                  f'must be a dict with "__type__" and "__value__" keys')

        try:
            t = value['__type__']
        except KeyError:
            raise ValidationError(f'Invalid Union[{",".join(self._serializers_by_name)}] value: {value}, '
                                  f'missing "__type__" key')
        try:
            v = value['__value__']
        except KeyError:
            raise ValidationError(f'Invalid Union[{",".join(self._serializers_by_name)}] value: {value}, '
                                  f'missing "__value__" key')
        try:
            serializer = self._serializers_by_name[t]
        except KeyError:
            raise ValidationError(f'Invalid Union[{",".join(self._serializers_by_name)}] value: {value}, '
                                  f'unsupported type.')
        return serializer.load(v, ctx)

    def dump(self, value: Any, ctx: Dumping) -> Dict:
        try:
            serializer = self._serializers_by_cls[type(value)]
        except KeyError:
            raise ValidationError(f'Invalid Union[{",".join(self._serializers_by_name)}] value: {value}')
        return {
            '__type__': type(value).__name__,
            '__value__': serializer.dump(value, ctx),
        }

    @classmethod
    def fits(cls, desc: TypeDescriptor) -> bool:
        return desc.cls is Union


class EnumSerializer(FieldSerializer[Any, Any]):
    """Enum value serializer. Note that output depends on enum value, so it can be `str`, `int`, etc.

    It is possible to serialize enums of non-S type if the enum is supplying this type as parent class.
    For example a date serialized to ISO string:

        :Example:

        class Date(date, Enum):
            TRINITY = 1945, 6, 16
            GAGARIN = 1961, 4, 11


        @dataclass(frozen=True)
        class HistoricEvent:
            name: str
            date: Date

        model = DictModel(HistoricEvent)
        dict = {'name': name, 'date': '1961-04-11'}
        dataclass = HistoricEvent(name, Date.GAGARIN)
        assert model.load(dict) == dataclass  # True
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._serializer = self._value_serializer()
        self._enum_values = {e.name for e in list(self.type.cls)}

    def _value_serializer(self) -> Optional[FieldSerializer]:
        cls = self.type.cls
        bases = cls.__bases__
        while len(bases) == 1:
            cls = bases[0]
            bases = cls.__bases__
        if len(bases) == 0:
            return None
        item_descriptor = self.type.describe(bases[0])
        return self.root.find_serializer(item_descriptor)

    def load(self, value: Any, ctx: Loading) -> Any:
        if self._serializer is None and value not in self._enum_values:
            raise ValidationError(f'"{value}" is not part of the {self.type.cls} enum')
        enum_cls = self.type.cls
        if self._serializer is not None:
            loaded_value = self._serializer.load(value, ctx)
            try:
                return enum_cls(loaded_value)
            except ValueError as e:
                raise ValidationError(f'"{value}" is not part of the {enum_cls} enum') from e
        return enum_cls[value]

    def dump(self, value: Any, ctx: Dumping) -> Any:
        if self._serializer is not None:
            return self._serializer.dump(value.value, ctx)
        return value.name

    @classmethod
    def fits(cls, desc: TypeDescriptor) -> bool:
        return issubclass(desc.cls, Enum)


class AnySerializer(FieldSerializer[Any, Any]):
    """Serializer for `Any` fields."""

    def load(self, value: Any, ctx: Loading) -> Any:
        return value

    def dump(self, value: Any, ctx: Dumping) -> Any:
        return value

    @classmethod
    def fits(cls, desc: TypeDescriptor) -> bool:
        return desc.cls is Any


class LiteralSerializer(FieldSerializer[Any, Any]):
    """Serializer for `Any` fields."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._dump_values = {
            v.cls: self.root.find_serializer(self.type.describe(v.cls.__class__)).dump(v, Dumping(validating=False))
            for v in self.type.parameters.values()
        }
        self._load_values = {
            value: key
            for key, value in self._dump_values.items()
        }

    def load(self, value: Any, ctx: Loading) -> Any:
        return value

    def dump(self, value: Any, ctx: Dumping) -> Any:
        return value

    @classmethod
    def fits(cls, desc: TypeDescriptor) -> bool:
        return desc.cls is Literal


class TypedDictSerializer(FieldSerializer[Dict[str, Any], Dict[str, Any]]):
    """Serializer for `TypedDict` fields."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._field_serializers = {}
        for field, desc in self.type.fields.items():
            self._field_serializers[field] = Alias(self.root.find_serializer(desc))

    @classmethod
    def fits(cls, desc: TypeDescriptor) -> bool:
        return desc.is_typed_dict

    def load(self, data: Dict[str, Any], ctx: Loading) -> Dict[str, Any]:
        if not isinstance(data, dict):
            raise ValidationError('Expecting a dictionary')
        items = self._serialize_typed_dict(data, ctx)
        return self.type.cls(items)

    def dump(self, data: Dict[str, Any], ctx: Dumping) -> Dict[str, Any]:
        return self._serialize_typed_dict(data, ctx)

    def _serialize_typed_dict(self, data: Dict[str, Any], ctx: Context) -> Dict[str, Any]:
        return {
            key: ctx.run(f'[key]', serializer(key), data[key])
            for key, serializer in self._field_serializers.items()
        }


class DictSerializer(FieldSerializer[Dict[str, Any], Dict[str, Any]]):
    """Serializer for `dict` fields with `str` keys (`Dict[str, Any]`)."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        key_desc = self.type.parameters[0]
        value_desc = self.type.parameters[1]
        assert not key_desc.is_optional, 'Dict keys must have explicit "str" type (Dict[str, Any]).'
        self._key_serializer = self.root.find_serializer(key_desc)
        self._value_serializer = self.root.find_serializer(value_desc)

    @classmethod
    def fits(cls, desc: TypeDescriptor) -> bool:
        return issubclass(desc.cls, dict) or issubclass(desc.cls, FrozenDict)

    def load(self, data: Dict[str, Any], ctx: Loading) -> Dict[str, Any]:
        if not isinstance(data, dict):
            raise ValidationError('Expecting a dictionary')
        items = self._serialize_dict(data, ctx)
        return self.type.cls(items)

    def dump(self, data: Dict[str, Any], ctx: Dumping) -> Dict[str, Any]:
        return self._serialize_dict(data, ctx)

    def _serialize_dict(self, data: Dict[str, Any], ctx: Context) -> Dict[str, Any]:
        key_serializer = Alias(self._key_serializer)
        value_serializer = Alias(self._value_serializer)
        return {
            ctx.run(f'#{key}', key_serializer(key), key): ctx.run(f'[{key}]', value_serializer(key), value)
            for key, value in data.items()
        }


Collection = Union[list, set, frozenset]


class CollectionSerializer(FieldSerializer[Collection, list]):
    """Serializer for lists, sets, and frozensets."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._serializer = self.root.find_serializer(self.type.parameters[0])
        self._item_type = self._serializer.type

    @classmethod
    def fits(cls, desc: TypeDescriptor) -> bool:
        return (issubclass(desc.cls, (list, set, frozenset, FrozenList))
                or (issubclass(desc.cls, tuple)
                    and len(desc.parameters) == 2
                    and desc.parameters[1].cls is Ellipsis))

    def load(self, value: list, ctx: Loading) -> Collection:
        if not isinstance(value, list):
            raise ValidationError(f'Expecting a list of {self._item_type.cls} values')
        items = self._serialize_collection(value, ctx)
        return self.type.cls(items)

    def dump(self, value: Collection, ctx: Dumping) -> list:
        return self._serialize_collection(value, ctx)

    def _serialize_collection(self, data: Any, ctx: Context) -> List[Any]:
        serializer = Alias(self._serializer)
        return [ctx.run(f'[{i}]', serializer(i), item) for i, item in enumerate(data)]


class TupleSerializer(FieldSerializer[tuple, list]):
    """Serializer for Python tuples."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._serializers = [self.root.find_serializer(self.type.parameters[i]) for i in self.type.parameters]
        self._size = len(self._serializers)

    @classmethod
    def fits(cls, desc: TypeDescriptor) -> bool:
        return issubclass(desc.cls, tuple)

    def load(self, value: list, ctx: Loading) -> tuple:
        if not isinstance(value, list):
            raise ValidationError(f'Expecting a list of {self._size} tuple values')
        if len(value) != self._size:
            raise ValidationError(f'Expecting a list of {self._size} tuple values')  # type: ignore
        items = self._serialize_tuple(value, ctx)
        return self.type.cls(items)

    def dump(self, value: tuple, ctx: Dumping) -> list:
        return self._serialize_tuple(value, ctx)

    def _serialize_tuple(self, data: Any, ctx: Context) -> List[Any]:
        serializer = OrdinalAlias(self._serializers)
        return [ctx.run(f'[{i}]', serializer(i), item) for i, item in enumerate(data)]


class Alias(Serializer):
    """Serializes values using the constructor parameter, but step name via calling instance as a function."""

    def __init__(self, serializer):
        self._serializer = serializer

    def __call__(self, key: Union[str, int]) -> Alias:
        self._key = key
        return self

    def step_name(self) -> str:
        return f'[{self._key}]'

    def load(self, value: Any, ctx: Loading) -> Any:
        return self._serializer.load(value, ctx)

    def dump(self, value: Any, ctx: Dumping) -> Any:
        return self._serializer.dump(value, ctx)


S = TypeVar("S", bound=Serializer)


class OrdinalAlias(Serializer[Any, Any]):
    """Serializes values using the provided serializer at the currently set index.
    The index is set via calling instance as a function.
    Step name is changed to match the index.
    """

    def __init__(self, serializers: List[S]):
        self._serializers = serializers

    def __call__(self, index: int) -> OrdinalAlias:
        self._index = index
        return self

    def step_name(self) -> str:
        return f'[{self._index}]'

    def load(self, value: Any, ctx: Loading) -> Any:
        return self._serializers[self._index].load(value, ctx)

    def dump(self, value: Any, ctx: Dumping) -> Any:
        return self._serializers[self._index].dump(value, ctx)


class BooleanSerializer(FieldSerializer[bool, bool]):
    """A serializer boolean field values."""

    @classmethod
    def fits(cls, desc: TypeDescriptor) -> bool:
        return issubclass(desc.cls, bool)

    def load(self, value: bool, ctx: Loading) -> bool:
        if not isinstance(value, bool):
            raise ValidationError(f"Invalid data type. Expecting boolean")
        return self.type.cls(value)

    def dump(self, value: bool, ctx: Dumping) -> bool:
        return bool(value)


class StringSerializer(FieldSerializer[str, str]):
    """A serializer for string field values."""

    @classmethod
    def fits(cls, desc: TypeDescriptor) -> bool:
        return issubclass(desc.cls, str)

    def load(self, value: str, ctx: Loading) -> str:
        if not isinstance(value, str):
            raise ValidationError('Invalid data type. Expecting a string')
        return self.type.cls(value)

    def dump(self, value: str, ctx: Dumping) -> str:
        return str(value)


class IntegerSerializer(FieldSerializer[int, int]):
    """A serializer for integer field values.

    .. note::
        In Python `bool` is a subclass of `int`, thus the check.
    """

    @classmethod
    def fits(cls, desc: TypeDescriptor) -> bool:
        return issubclass(desc.cls, int) and not issubclass(desc.cls, bool)

    def load(self, value: int, ctx: Loading) -> int:
        if not isinstance(value, int) or isinstance(value, bool):
            raise ValidationError('Invalid data type. Expecting an integer')
        return self.type.cls(value)

    def dump(self, value: int, ctx: Dumping) -> int:
        return int(value)


class FloatSerializer(FieldSerializer[float, float]):
    """A serializer for float values field values.

    During load this can be either an int (1) or float (1.0). Always dumps to float."""

    @classmethod
    def fits(cls, desc: TypeDescriptor) -> bool:
        return issubclass(desc.cls, float)

    def load(self, value: float, ctx: Loading) -> float:
        is_numeric = isinstance(value, (int, float)) and not isinstance(value, bool)
        if not is_numeric:
            raise ValidationError('Invalid data type. Expecting a numeric value')
        return self.type.cls(value)

    def dump(self, value: float, ctx: Dumping) -> float:
        return float(value)


class DataclassSerializer(FieldSerializer[Any, Dict[str, Any]]):
    """A serializer for field values that are dataclasses instances."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._serializer = self.root.child_model(self.type)
        self._dc_name = self.type.cls.__name__

    @classmethod
    def fits(cls, desc: TypeDescriptor) -> bool:
        return desc.is_dataclass

    def load(self, value: Dict[str, Any], ctx: Loading) -> Any:
        if not isinstance(value, dict):
            raise ValidationError(f'Invalid data type. Expecting a mapping matching {self._dc_name} model')
        return self._serializer.load(value, ctx)  # type: ignore # type: ignore # value always a mapping

    def dump(self, value: Any, ctx: Dumping) -> Dict[str, Any]:
        return self._serializer.dump(value, ctx)


class UtcTimestampSerializer(FieldSerializer[Timestamp, Union[float, int]]):
    """A serializer of UTC timestamp field values to/from float value.

        :Example:

        from serious.types import timestamp

        @dataclass
        class Transaction:
            created_at: timestamp

        transaction = Transaction(timestamp(1542473728.456753))

    Dumping the `post` will return `{"created_at": 1542473728.456753}`.
    """

    @classmethod
    def fits(cls, desc: TypeDescriptor) -> bool:
        return issubclass(desc.cls, Timestamp)

    def load(self, value: Union[float, int], ctx: Loading) -> Timestamp:
        if not isinstance(value, (int, float)):
            raise ValidationError('Invalid data type. Expecting int or float')
        return Timestamp(value)  # type: ignore # expecting float

    def dump(self, value: Timestamp, ctx: Dumping) -> float:
        return value.value


_iso_date_time_re = re.compile(  # https://stackoverflow.com/a/43931246/8677389
    r'\A(?:\d{4}-(?:(?:0[1-9]|1[0-2])-(?:0[1-9]|1\d|2[0-8])|(?:0[13-9]|1[0-2])-(?:29|30)|(?:0[13578]|1[02])-31)'
    r'|(?:[1-9]\d(?:0[48]|[2468][048]|[13579][26])|(?:[2468][048]|[13579][26])00)-02-29)'
    r'T(?:[01]\d|2[0-3]):[0-5]\d:[0-5]\d(?:\.\d{1,9})?(?:Z|[+-][01]\d:[0-5]\d)?\Z'
)
_iso_date_re = re.compile(
    r'\A(?P<year>[0-9]{4})(?P<hyphen>-?)(?P<month>1[0-2]|0[1-9])(?P=hyphen)(?P<day>3[01]|0[1-9]|[12][0-9])\Z'
)
_iso_time_re = re.compile(
    r'\A(?P<hour>2[0-3]|[01][0-9])'
    r':?(?P<minute>[0-5][0-9])'
    r':?(?P<second>[0-5][0-9])'
    r'(?P<timezone>Z|[+-](?:2[0-3]|[01][0-9])(?::?(?:[0-5][0-9]))?)?\Z'
)


class DateTimeIsoSerializer(FieldSerializer[datetime, str]):
    """A serializer for datetime field values to a timestamp represented by a `ISO formatted string`_.

        :Example:

        @dataclass
        class Post:
            timestamp: datetime

        timestamp = datetime(2018, 11, 17, 16, 55, 28, 456753, tzinfo=timezone.utc)
        post = Post(timestamp)

    Dumping the `post` will return `'{"timestamp": "2018-11-17T16:55:28.456753+00:00"}'`.

    .. _ISO formatted string: https://en.wikipedia.org/wiki/ISO_8601
    """

    def load(self, value: str, ctx: Loading) -> datetime:
        if not isinstance(value, str):
            raise ValidationError('Invalid data type. Expecting a string')
        if not _matches(_iso_date_time_re, value):
            raise ValidationError('Invalid date/time format. Check the ISO 8601 specification')
        return datetime.fromisoformat(value)  # type: ignore # expecting datetime

    def dump(self, value: datetime, ctx: Dumping) -> str:
        return datetime.isoformat(value)

    @classmethod
    def fits(cls, desc: TypeDescriptor) -> bool:
        return issubclass(desc.cls, datetime)


class DateIsoSerializer(FieldSerializer[date, str]):
    """A serializer of `date` field values to a timestamp represented by an `ISO formatted string`_.

        :Example:

        @dataclass
        class Event:
            name: str
            when: date

        event = Event('Albert Einstein won Nobel Prize in Physics', date(1922, 9, 9))

    Dumping the `event` will return `'{"name": "…", "when": "1922-09-09"}'`.

    .. _ISO formatted string: https://en.wikipedia.org/wiki/ISO_8601
    """

    def load(self, value: str, ctx: Loading) -> date:
        if not isinstance(value, str):
            raise ValidationError('Invalid data type. Expecting a string')
        if not _matches(_iso_date_re, value):
            raise ValidationError('Invalid date format. Check the ISO 8601 specification')
        return date.fromisoformat(value)  # type: ignore # expecting datetime

    def dump(self, value: date, ctx: Dumping) -> str:
        return date.isoformat(value)

    @classmethod
    def fits(cls, desc: TypeDescriptor) -> bool:
        return issubclass(desc.cls, date)


class TimeIsoSerializer(FieldSerializer[time, str]):
    """A serializer for `time` field values to an `ISO formatted string`_.

        :Example:

        @dataclass
        class Alarm:
            at: time
            enabled: bool

        alarm = Alarm(time(7, 0, 0), enabled=True)

    Dumping the `post` will return `'{"at": "07:00:00", "enabled": True}'`.

    .. _ISO formatted string: https://en.wikipedia.org/wiki/ISO_8601
    """

    def load(self, value: str, ctx: Loading) -> time:
        if not isinstance(value, str):
            raise ValidationError('Invalid data type. Expecting a string')
        if not _matches(_iso_time_re, value):
            raise ValidationError('Invalid time format. Check the ISO 8601 specification')
        return time.fromisoformat(value)  # type: ignore # expecting datetime

    def dump(self, value: time, ctx: Dumping) -> str:
        return time.isoformat(value)

    @classmethod
    def fits(cls, desc: TypeDescriptor) -> bool:
        return issubclass(desc.cls, time)


_uuid_hex_re = re.compile(r'\A([a-f0-9]{8}-?[a-f0-9]{4}-?[a-f0-9]{4}-?[a-f0-9]{4}-?[a-f0-9]{12})\Z', re.I)


class UuidSerializer(FieldSerializer[UUID, str]):
    """A `UUID` value serializer to `str`."""

    def load(self, value: str, ctx: Loading) -> UUID:
        if not isinstance(value, str):
            raise ValidationError('Invalid data type. Expecting a string')
        if not _matches(_uuid_hex_re, value):
            raise ValidationError('Invalid UUID hex format')
        return UUID(value)  # type: ignore # expecting str

    def dump(self, value: UUID, ctx: Dumping) -> str:
        return str(value)

    @classmethod
    def fits(cls, desc: TypeDescriptor) -> bool:
        return issubclass(desc.cls, UUID)


_decimal_re = re.compile(r'\A\d+(\.\d+)?\Z')


class DecimalSerializer(FieldSerializer[Decimal, str]):
    """`Decimal` value serializer to `str`."""

    def load(self, value: str, ctx: Loading) -> Decimal:
        if not isinstance(value, str):
            raise ValidationError('Invalid data type. Expecting a string')
        if not _matches(_decimal_re, value):
            raise ValidationError('Invalid decimal format. A number with a "." as a decimal separator is expected')
        return Decimal(value)  # type: ignore # expecting str

    def dump(self, value: Decimal, ctx: Dumping) -> str:
        return str(value)

    @classmethod
    def fits(cls, desc: TypeDescriptor) -> bool:
        return issubclass(desc.cls, Decimal)


def _matches(regex: Pattern, value: str) -> bool:
    return regex.match(value) is not None  # type: ignore # caller ensures str
