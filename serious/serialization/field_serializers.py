from __future__ import annotations

__all__ = [
    "field_serializers",
    "OptionalSerializer",
    "AnySerializer",
    "EnumSerializer",
    "DictSerializer",
    "CollectionSerializer",
    "TupleSerializer",
    "StringSerializer",
    "BooleanSerializer",
    "IntegerSerializer",
    "FloatSerializer",
    "DataclassSerializer",
    "UtcTimestampSerializer",
    "DateTimeIsoSerializer",
    "DateIsoSerializer",
    "TimeIsoSerializer",
    "UuidSerializer",
    "DecimalSerializer",
]

import re
from dataclasses import replace
from datetime import datetime, date, time
from decimal import Decimal
from enum import Enum
from types import UnionType
from typing import (
    Any,
    Optional,
    Dict,
    List,
    Union,
    Pattern,
    Iterable,
    Type,
    Tuple,
    Literal,
)
from uuid import UUID

from serious.descriptors import Descriptor
from serious.errors import ValidationError
from serious.types import Timestamp, FrozenList, FrozenDict
from .context import SerializationContext
from .serializer import Serializer


def field_serializers(
    custom: Iterable[Type[Serializer]] = tuple(),
) -> Tuple[Type[Serializer], ...]:
    """Default list of Serious field serializers.

    Returns a frozen collection of field serializers in the default order.
    You can provide a list of custom field serializers to include them along with default serializers.
    The order in the collection defines the order in which the serializers will be tested for fitness for each field.

    :param custom: a list of custom serializers which are injected into the default list

    """

    extras: List[Type[Serializer]] = []

    if SQLALCHEMY_INTEGRATION_ENABLED:
        extras.append(SqlAlchemyDeclarativeSerializer)

    if PYDANTIC_INTEGRATION_ENABLED:
        extras.append(PydanticModelSerializer)

    return tuple(
        [
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
            *extras,
        ]
    )


class OptionalSerializer(Serializer[Optional[Any], Optional[Any]]):
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

    def load(
        self, primitive: Optional[Any], ctx: SerializationContext
    ) -> Optional[Any]:
        return None if primitive is None else self._serializer.load(primitive, ctx)

    def dump(self, value: Optional[Any], ctx: SerializationContext) -> Optional[Any]:
        return None if value is None else self._serializer.dump(value, ctx)

    @classmethod
    def fits(cls, desc: Descriptor) -> bool:
        return desc.is_optional


class UnionSerializer(Serializer[Any, Dict]):
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
            desc.cls: self.root.find_serializer(desc)
            for desc in self.type.parameters.values()
        }
        self._serializers_by_name = {
            cls.__name__: serializer
            for cls, serializer in self._serializers_by_cls.items()
        }

    def load(self, value: Dict, ctx: SerializationContext) -> Any:
        try:
            value = dict(value)
        except TypeError:
            raise ValidationError(
                f'Invalid Union[{",".join(self._serializers_by_name)}] value: {value}, '
                f'must be a dict with "__type__" and "__value__" keys'
            )

        try:
            t = value["__type__"]
        except KeyError:
            raise ValidationError(
                f'Invalid Union[{",".join(self._serializers_by_name)}] value: {value}, '
                f'missing "__type__" key'
            )
        try:
            v = value["__value__"]
        except KeyError:
            raise ValidationError(
                f'Invalid Union[{",".join(self._serializers_by_name)}] value: {value}, '
                f'missing "__value__" key'
            )
        try:
            serializer = self._serializers_by_name[t]
        except KeyError:
            raise ValidationError(
                f'Invalid Union[{",".join(self._serializers_by_name)}] value: {value}, '
                f"unsupported type."
            )
        return serializer.load(v, ctx)

    def dump(self, value: Any, ctx: SerializationContext) -> Dict:
        try:
            serializer = self._serializers_by_cls[type(value)]
        except KeyError:
            raise ValidationError(
                f'Invalid Union[{",".join(self._serializers_by_name)}] value: {value}'
            )
        return {
            "__type__": type(value).__name__,
            "__value__": serializer.dump(value, ctx),
        }

    @classmethod
    def fits(cls, desc: Descriptor) -> bool:
        return desc.cls is Union or isinstance(desc.cls, UnionType)


class EnumSerializer(Serializer[Any, Any]):
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

    def _value_serializer(self) -> Optional[Serializer]:
        cls = self.type.cls
        bases = cls.__bases__
        while len(bases) == 1:
            cls = bases[0]
            bases = cls.__bases__
        if len(bases) == 0:
            return None
        item_descriptor = self.type.describe(bases[0])
        return self.root.find_serializer(item_descriptor)

    def load(self, primitive, ctx) -> Any:
        if self._serializer is None and primitive not in self._enum_values:
            raise ValidationError(
                f'"{primitive}" is not part of the {self.type.cls} enum'
            )
        enum_cls = self.type.cls
        if self._serializer is not None:
            loaded_value = self._serializer.load(primitive, ctx)
            try:
                return enum_cls(loaded_value)
            except ValueError as e:
                raise ValidationError(
                    f'"{primitive}" is not part of the {enum_cls} enum'
                ) from e
        return enum_cls[primitive]

    def dump(self, value, ctx) -> Any:
        if self._serializer is not None:
            return self._serializer.dump(value.value, ctx)
        return value.name

    @classmethod
    def fits(cls, desc: Descriptor) -> bool:
        return issubclass(desc.cls, Enum)


class AnySerializer(Serializer[Any, Any]):
    """Serializer for `Any` fields."""

    def load(self, value, _):
        return value

    def dump(self, value, _):
        return value

    @classmethod
    def fits(cls, desc: Descriptor) -> bool:
        return desc.cls is Any


class LiteralSerializer(Serializer[Any, Any]):
    """Serializer for `Any` fields."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._dump_values = {
            v.cls: self.root.find_serializer(self.type.describe(v.cls.__class__)).dump(
                v, SerializationContext([], False)
            )
            for v in self.type.parameters.values()
        }
        self._load_values = {value: key for key, value in self._dump_values.items()}

    def load(self, value, _) -> Any:
        return value

    def dump(self, value, _) -> Any:
        return value

    @classmethod
    def fits(cls, desc: Descriptor) -> bool:
        return desc.cls is Literal


class TypedDictSerializer(Serializer[Dict[str, Any], Dict[str, Any]]):
    """Serializer for `TypedDict` fields."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._field_serializers = {}
        for field, desc in self.type.fields.items():
            self._field_serializers[field] = self.root.find_serializer(desc)

    @classmethod
    def fits(cls, desc: Descriptor) -> bool:
        return desc.is_typed_dict

    def load(self, data: Dict[str, Any], ctx: SerializationContext) -> Dict[str, Any]:
        if not isinstance(data, dict):
            raise ValidationError("Expecting a dictionary")
        if missing := {field for field in self._field_serializers if field not in data}:
            raise ValidationError(f"Missing fields: {missing}")
        items = {
            key: serializer.load_nested(f"[key]", data[key], ctx)
            for key, serializer in self._field_serializers.items()
        }
        return self.type.cls(items)

    def dump(self, data: Dict[str, Any], ctx: SerializationContext) -> Dict[str, Any]:
        if missing := {field for field in self._field_serializers if field not in data}:
            raise ValidationError(f"Missing fields: {missing}")
        return {
            key: serializer.dump_nested(f"[key]", data[key], ctx)
            for key, serializer in self._field_serializers.items()
        }


class DictSerializer(Serializer[Dict[str, Any], Dict[str, Any]]):
    """Serializer for `dict` fields with `str` keys (`Dict[str, Any]`)."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        key_desc = self.type.parameters[0]
        value_desc = self.type.parameters[1]
        assert (
            not key_desc.is_optional
        ), 'Dict keys must have explicit "str" type (Dict[str, Any]).'
        self._key_serializer = self.root.find_serializer(key_desc)
        self._value_serializer = self.root.find_serializer(value_desc)

    @classmethod
    def fits(cls, desc: Descriptor) -> bool:
        return issubclass(desc.cls, dict) or issubclass(desc.cls, FrozenDict)

    def load(self, data: Dict[str, Any], ctx: SerializationContext) -> Dict[str, Any]:
        if not isinstance(data, dict):
            raise ValidationError("Expecting a dictionary")
        items = {
            self._key_serializer.load_nested(
                f"#{key}", key, ctx
            ): self._value_serializer.load_nested(f"[{key}]", value, ctx)
            for key, value in data.items()
        }

        return self.type.cls(items)

    def dump(self, data: Dict[str, Any], ctx: SerializationContext) -> Dict[str, Any]:
        return {
            self._key_serializer.dump_nested(
                f"#{key}", key, ctx
            ): self._value_serializer.dump_nested(f"[{key}]", value, ctx)
            for key, value in data.items()
        }


SOME_COLLECTION = Union[list, set, frozenset]


class CollectionSerializer(Serializer[SOME_COLLECTION, list]):
    """Serializer for lists, sets, and frozensets."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._serializer = self.root.find_serializer(self.type.parameters[0])
        self._item_type = self._serializer.type

    @classmethod
    def fits(cls, desc: Descriptor) -> bool:
        return issubclass(desc.cls, (list, set, frozenset, FrozenList)) or (
            issubclass(desc.cls, tuple)
            and len(desc.parameters) == 2
            and desc.parameters[1].cls is Ellipsis
        )

    def load(self, primitive: list, ctx: SerializationContext) -> SOME_COLLECTION:
        if not isinstance(primitive, (list, set, tuple, FrozenList)):
            raise ValidationError(f"Expecting a list of {self._item_type.cls} values")
        items = [
            self._serializer.load_nested(f"[{i}]", item, ctx)
            for i, item in enumerate(primitive)
        ]
        return self.type.cls(items)

    def dump(self, o: SOME_COLLECTION, ctx: SerializationContext) -> list:
        return [
            self._serializer.dump_nested(f"[{i}]", item, ctx)
            for i, item in enumerate(o)
        ]


class TupleSerializer(Serializer[tuple, list]):
    """Serializer for Python tuples."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._serializers = [
            self.root.find_serializer(self.type.parameters[i])
            for i in self.type.parameters
        ]
        self._size = len(self._serializers)

    @classmethod
    def fits(cls, desc: Descriptor) -> bool:
        return issubclass(desc.cls, tuple)

    def load(self, primitive: list, ctx: SerializationContext) -> tuple:
        if not isinstance(primitive, list):
            raise ValidationError(f"Expecting a list of {self._size} tuple values")
        if len(primitive) != self._size:
            raise ValidationError(f"Expecting a list of {self._size} tuple values")  # type: ignore
        items = [
            self._serializers[i].load_nested(f"[{i}]", item, ctx)
            for i, item in enumerate(primitive)
        ]
        return self.type.cls(items)

    def dump(self, value: tuple, ctx: SerializationContext) -> list:
        return [
            self._serializers[i].dump_nested(f"[{i}]", item, ctx)
            for i, item in enumerate(value)
        ]


class BooleanSerializer(Serializer[bool, bool]):
    """A serializer boolean field values."""

    @classmethod
    def fits(cls, desc: Descriptor) -> bool:
        return issubclass(desc.cls, bool)

    def load(self, value, _) -> bool:
        if not isinstance(value, bool):
            raise ValidationError(f"Invalid data type. Expecting boolean")
        return self.type.cls(value)

    def dump(self, value, _) -> bool:
        return bool(value)


class StringSerializer(Serializer[str, str]):
    """A serializer for string field values."""

    @classmethod
    def fits(cls, desc: Descriptor) -> bool:
        return issubclass(desc.cls, str)

    def load(self, value: str, _) -> str:
        if not isinstance(value, str):
            raise ValidationError("Invalid data type. Expecting a string")
        return self.type.cls(value)

    def dump(self, value: str, _) -> str:
        return str(value)


class IntegerSerializer(Serializer[int, int]):
    """A serializer for integer field values.

    .. note::
        In Python `bool` is a subclass of `int`, thus the check.
    """

    @classmethod
    def fits(cls, desc: Descriptor) -> bool:
        return issubclass(desc.cls, int) and not issubclass(desc.cls, bool)

    def load(self, value: int, _) -> int:
        if not isinstance(value, int) or isinstance(value, bool):
            raise ValidationError("Invalid data type. Expecting an integer")
        return self.type.cls(value)

    def dump(self, value: int, _) -> int:
        return int(value)


class FloatSerializer(Serializer[float, float]):
    """A serializer for float values field values.

    During load this can be either an int (1) or float (1.0). Always dumps to float."""

    @classmethod
    def fits(cls, desc: Descriptor) -> bool:
        return issubclass(desc.cls, float)

    def load(self, value: float, _) -> float:
        is_numeric = isinstance(value, (int, float)) and not isinstance(value, bool)
        if not is_numeric:
            raise ValidationError("Invalid data type. Expecting a numeric value")
        return self.type.cls(value)

    def dump(self, value: float, _) -> float:
        return float(value)


class DataclassSerializer(Serializer[Any, Dict[str, Any]]):
    """A serializer for field values that are dataclasses instances."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._serializer = self.root.child_model(self.type)
        self._dc_name = self.type.cls.__name__

    @classmethod
    def fits(cls, desc: Descriptor) -> bool:
        return desc.is_dataclass

    def load(self, primitive: Dict[str, Any], ctx: SerializationContext) -> Any:
        if not isinstance(primitive, dict):
            raise ValidationError(
                f"Invalid data type. Expecting a mapping matching {self._dc_name} model"
            )
        return self._serializer.load(primitive, ctx)  # type: ignore # value always a mapping

    def dump(self, value: Any, ctx: SerializationContext) -> Dict[str, Any]:
        return self._serializer.dump(value, ctx)


class UtcTimestampSerializer(Serializer[Timestamp, Union[float, int]]):
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
    def fits(cls, desc: Descriptor) -> bool:
        return issubclass(desc.cls, Timestamp)

    def load(self, value: Union[float, int], _) -> Timestamp:
        if not isinstance(value, (int, float)):
            raise ValidationError("Invalid data type. Expecting int or float")
        return Timestamp(value)  # type: ignore # expecting float

    def dump(self, value: Timestamp, _) -> float:
        return value.value


_iso_date_time_re = re.compile(  # https://stackoverflow.com/a/43931246/8677389
    r"\A(?:\d{4}-(?:(?:0[1-9]|1[0-2])-(?:0[1-9]|1\d|2[0-8])|(?:0[13-9]|1[0-2])-(?:29|30)|(?:0[13578]|1[02])-31)"
    r"|(?:[1-9]\d(?:0[48]|[2468][048]|[13579][26])|(?:[2468][048]|[13579][26])00)-02-29)"
    r"T(?:[01]\d|2[0-3]):[0-5]\d:[0-5]\d(?:\.\d{1,9})?(?:Z|[+-][01]\d:[0-5]\d)?\Z"
)
_iso_date_re = re.compile(
    r"\A(?P<year>[0-9]{4})(?P<hyphen>-?)(?P<month>1[0-2]|0[1-9])(?P=hyphen)(?P<day>3[01]|0[1-9]|[12][0-9])\Z"
)
_iso_time_re = re.compile(
    r"\A(?P<hour>2[0-3]|[01][0-9])"
    r":?(?P<minute>[0-5][0-9])"
    r":?(?P<second>[0-5][0-9])"
    r"(?P<timezone>Z|[+-](?:2[0-3]|[01][0-9])(?::?(?:[0-5][0-9]))?)?\Z"
)


class DateTimeIsoSerializer(Serializer[datetime, str]):
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

    def load(self, value: str, _) -> datetime:
        if not isinstance(value, str):
            raise ValidationError("Invalid data type. Expecting a string")
        if not _matches(_iso_date_time_re, value):
            raise ValidationError(
                "Invalid date/time format. Check the ISO 8601 specification"
            )
        return datetime.fromisoformat(value)  # type: ignore # expecting datetime

    def dump(self, value: datetime, _) -> str:
        return datetime.isoformat(value)

    @classmethod
    def fits(cls, desc: Descriptor) -> bool:
        return issubclass(desc.cls, datetime)


class DateIsoSerializer(Serializer[date, str]):
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

    def load(self, value: str, _) -> date:
        if not isinstance(value, str):
            raise ValidationError("Invalid data type. Expecting a string")
        if not _matches(_iso_date_re, value):
            raise ValidationError(
                "Invalid date format. Check the ISO 8601 specification"
            )
        return date.fromisoformat(value)  # type: ignore # expecting datetime

    def dump(self, value: date, _) -> str:
        return date.isoformat(value)

    @classmethod
    def fits(cls, desc: Descriptor) -> bool:
        return issubclass(desc.cls, date)


class TimeIsoSerializer(Serializer[time, str]):
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

    def load(self, value: str, _) -> time:
        if not isinstance(value, str):
            raise ValidationError("Invalid data type. Expecting a string")
        if not _matches(_iso_time_re, value):
            raise ValidationError(
                "Invalid time format. Check the ISO 8601 specification"
            )
        return time.fromisoformat(value)  # type: ignore # expecting datetime

    def dump(self, value: time, _) -> str:
        return time.isoformat(value)

    @classmethod
    def fits(cls, desc: Descriptor) -> bool:
        return issubclass(desc.cls, time)


_uuid_hex_re = re.compile(
    r"\A([a-f0-9]{8}-?[a-f0-9]{4}-?[a-f0-9]{4}-?[a-f0-9]{4}-?[a-f0-9]{12})\Z", re.I
)


class UuidSerializer(Serializer[UUID, str]):
    """A `UUID` value serializer to `str`."""

    def load(self, value: str, _) -> UUID:
        if not isinstance(value, str):
            raise ValidationError("Invalid data type. Expecting a string")
        if not _matches(_uuid_hex_re, value):
            raise ValidationError("Invalid UUID hex format")
        return UUID(value)  # type: ignore # expecting str

    def dump(self, value: UUID, _) -> str:
        return str(value)

    @classmethod
    def fits(cls, desc: Descriptor) -> bool:
        return issubclass(desc.cls, UUID)


_decimal_re = re.compile(r"\A\d+(\.\d+)?\Z")


class DecimalSerializer(Serializer[Decimal, str]):
    """`Decimal` value serializer to `str`."""

    def load(self, value: str, _) -> Decimal:
        if not isinstance(value, str):
            raise ValidationError("Invalid data type. Expecting a string")
        if not _matches(_decimal_re, value):
            raise ValidationError(
                'Invalid decimal format. A number with a "." as a decimal separator is expected'
            )
        return Decimal(value)  # type: ignore # expecting str

    def dump(self, value: Decimal, _) -> str:
        return str(value)

    @classmethod
    def fits(cls, desc: Descriptor) -> bool:
        return issubclass(desc.cls, Decimal)


def _matches(regex: Pattern, value: str) -> bool:
    return regex.match(value) is not None  # type: ignore # caller ensures str


try:
    from sqlalchemy.orm import DeclarativeMeta

    SQLALCHEMY_INTEGRATION_ENABLED = True

    class SqlAlchemyDeclarativeSerializer(
        Serializer[DeclarativeMeta, Dict[str, Any]]
    ):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self._field_serializers = {}
            for field, desc in self.type.fields.items():
                if not (
                    desc.is_sqlalchemy_model
                    or any(p.is_sqlalchemy_model for p in desc.parameters.values())
                ):
                    self._field_serializers[field] = self.root.find_serializer(desc)

        @classmethod
        def fits(cls, desc: Descriptor) -> bool:
            return desc.is_sqlalchemy_model

        def load(
            self, data: Dict[str, Any], ctx: SerializationContext
        ) -> DeclarativeMeta:
            if not isinstance(data, dict):
                raise ValidationError("Expecting a dictionary")
            if missing := {
                field for field in self._field_serializers if field not in data
            }:
                raise ValidationError(f"Missing fields: {missing}")
            items = {
                key: serializer.load_nested(f".{key}", data[key], ctx)
                for key, serializer in self._field_serializers.items()
            }
            return self.type.cls(**items)

        def dump(
            self, data: DeclarativeMeta, ctx: SerializationContext
        ) -> Dict[str, Any]:
            return {
                key: serializer.dump_nested(f".{key}", getattr(data, key), ctx)
                for key, serializer in self._field_serializers.items()
            }

except ImportError:
    SQLALCHEMY_INTEGRATION_ENABLED = False

try:
    from pydantic import BaseModel

    PYDANTIC_INTEGRATION_ENABLED = True

    class PydanticModelSerializer(Serializer[BaseModel, str]):
        @classmethod
        def fits(cls, desc: Descriptor) -> bool:
            return issubclass(desc.cls, BaseModel)

        def dump(self, value: BaseModel, _) -> str:
            return value.json()

        def load(self, value: str, _) -> BaseModel:
            return self.type.cls.parse_raw(value)

except ImportError:
    PYDANTIC_INTEGRATION_ENABLED = False
