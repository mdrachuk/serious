from __future__ import annotations

from abc import abstractmethod, ABC
from dataclasses import replace
from datetime import datetime, date, time
from decimal import Decimal
from enum import Enum
from typing import Any, Type, Iterable, List
from uuid import UUID

from serious.context import SerializationContext as Context, SerializationStep
from serious.descriptors import FieldDescriptor
from serious.types import frozenlist, FrozenList, Timestamp, timestamp
from serious.utils import Primitive

if False:  # To reference in typings
    from serious.schema import SeriousSchema


class FieldSerializer(SerializationStep, ABC):
    """
    A abstract field serializer defining a constructor invoked by serious, [dump](#dump)/[load](#load)
    and class [fits](#fits) methods.

    Field serializers are provided to a serious schema ([JsonSchema][1], [DictSchema][2], [YamlSchema][3]) serializers
    parameter in an order in which they will be tested for fitness in.

    A clean way to add custom serializers to the defaults is to use the [field_serializers] function.

    [1]: serious.json.api.JsonSchema
    [2]: serious.dict.api.DictSchema
    [3]: serious.yaml.api.YamlSchema
    """

    def __init__(self, field: FieldDescriptor, sr: SeriousSchema):
        self._field = field
        self._sr = sr

    @classmethod
    @abstractmethod
    def fits(cls, field: FieldDescriptor) -> bool:
        """
        A predicate returning `True` if this serializer should load/dump data for the provided field.

        Beware, the the `field.type.cls` property can be an instance of a generic alias which will error,
        if using `issubclass` which expects a `type`.
        """
        raise NotImplementedError(f"Serializer {cls} must implement the `#fits(FieldDescriptor)` method.")

    def step_name(self):
        return f'.{self.field.name}'

    @property
    def field(self) -> FieldDescriptor:
        """Read access to the field processed by the serializer."""
        return self._field

    @abstractmethod
    def dump(self, value: Any, ctx: Context) -> Primitive:
        raise NotImplementedError

    @abstractmethod
    def load(self, value: Primitive, ctx: Context) -> Any:
        raise NotImplementedError


def field_serializers(custom: Iterable[Type[FieldSerializer]] = tuple()) -> FrozenList[Type[FieldSerializer]]:
    """
    A tuple of field serializers in a default order.
    Provide a custom list of field serializers to include them after metadata and optional serializers.
    The order in the collection defines the order in which the serializers will be tested for fitness for each field.
    """
    return frozenlist([
        MetadataSerializer,
        OptionalSerializer,
        AnySerializer,
        EnumSerializer,
        *custom,
        DictSerializer,
        CollectionSerializer,
        TupleSerializer,
        PrimitiveSerializer,
        DataclassSerializer,
        DateTimeUtcTimestampSerializer,
        DateTimeIsoSerializer,
        DateIsoSerializer,
        TimeIsoSerializer,
        UuidSerializer,
        DecimalSerializer,
    ])


class MetadataSerializer(FieldSerializer):
    """
    A serializer using the `load` and `dump` provided to dataclass fields metadata.

    Example where we’re hiding the email when dumping data to send to client:
    ```python
    @dataclass
    class PersonalContact:
        email: Email = field(
            metadata={'serious': {
                'dump': lambda value: '...@' + value.split("@")[1],
                'load': lambda data: data,
            }})
    ```
    """

    def __init__(self, field: FieldDescriptor, sr: SeriousSchema):
        super().__init__(field, sr)
        metadata = field.metadata['serious']
        self._load = metadata['load']
        self._dump = metadata['dump']

    def load(self, value: Primitive, ctx: Context) -> Any:
        return self._load(value)

    def dump(self, value: Any, ctx: Context) -> Primitive:
        return self._dump(value)

    @classmethod
    def fits(cls, field: FieldDescriptor) -> bool:
        return field.metadata is not None and 'serious' in field.metadata


class OptionalSerializer(FieldSerializer):
    """
    A serializer for field marked as [Optional]. An optional field has internally a serializer for the target type,
    but first checks if the loaded data is `None`.

    Example:
    ```python
    @dataclass
    class Node:
        node: Optional[Node]
    ```
    """

    def __init__(self, field: FieldDescriptor, sr: SeriousSchema):
        super().__init__(field, sr)
        item_descriptor = replace(field, type=replace(field.type, is_optional=False))
        self._serializer = sr.field_serializer(item_descriptor)

    def dump(self, value: Any, ctx: Context) -> Primitive:
        return None if value is None else self._serializer.dump(value, ctx)

    def load(self, value: Primitive, ctx: Context) -> Any:
        return None if value is None else self._serializer.load(value, ctx)

    @classmethod
    def fits(cls, field: FieldDescriptor) -> bool:
        return field.type.is_optional


class EnumSerializer(FieldSerializer):
    """Enum value serializer. Note that output depends on enum value, so it can be `str`, `int`, etc.

    It is possible to serialize enums of non-primitive type if the enum is supplying this type as parent class.
    For example a date serialized to ISO string:
    ```python
    class Date(date, Enum):
        TRINITY = 1945, 6, 16
        GAGARIN = 1961, 4, 11


    @dataclass(frozen=True)
    class HistoricEvent:
        name: str
        date: Date

    schema = DictSchema(HistoricEvent)
    dict = {'name': name, 'date': '1961-04-11'}
    dataclass = HistoricEvent(name, Date.GAGARIN)
    assert schema.load(dict) == dataclass  # True
    ```"""

    def __init__(self, field: FieldDescriptor, sr: SeriousSchema):
        super().__init__(field, sr)
        cls = field.type.cls
        bases = cls.__bases__
        while len(bases) == 1:
            cls = bases[0]
            bases = cls.__bases__
        if len(bases) == 0:
            self._serializer = None
        else:
            item_descriptor = replace(field, type=field.type.describe(bases[0]))
            self._serializer = sr.field_serializer(item_descriptor)

    def load(self, value: Primitive, ctx: Context) -> Any:
        enum_cls = self.field.type.cls
        if self._serializer is not None:
            loaded_value = self._serializer.load(value, ctx)
            return enum_cls(loaded_value)
        return enum_cls(value)

    def dump(self, value: Any, ctx: Context) -> Primitive:
        enum_value = value.value
        if self._serializer is not None:
            return self._serializer.dump(enum_value, ctx)
        return enum_value

    @classmethod
    def fits(cls, field: FieldDescriptor) -> bool:
        return issubclass(field.type.cls, Enum)


class AnySerializer(FieldSerializer):
    """Serializer for [Any] fields."""

    def load(self, value: Primitive, ctx: Context) -> Any:
        return value

    def dump(self, value: Any, ctx: Context) -> Primitive:
        return value

    @classmethod
    def fits(cls, field: FieldDescriptor) -> bool:
        return field.type.cls is Any


class DictSerializer(FieldSerializer):
    """Serializer for `dict` fields with `str` keys (Dict[str, Any])."""

    def __init__(self, field: FieldDescriptor, sr: SeriousSchema):
        super().__init__(field, sr)
        key = field.type.parameters[0]
        assert key.cls is str and not key.is_optional, 'Dict keys must have explicit str type (Dict[str, Any]).'
        self._val_sr = generic_item_serializer(field, sr, param_index=1)

    @classmethod
    def fits(cls, field: FieldDescriptor) -> bool:
        return issubclass(field.type.cls, dict)

    def load(self, data: Primitive, ctx: Context) -> Any:
        items = {
            key: self.load_value(key, value, ctx)
            for key, value in data.items()  # type: ignore # data is always a dict
        }
        return self.field.type.cls(items)

    def dump(self, d: Any, ctx: Context) -> Primitive:
        return {key: self.dump_value(key, value, ctx) for key, value in d.items()}

    def load_value(self, key, value: Primitive, ctx: Context) -> Any:
        with ctx.enter(CollectionStep(key)):
            return self._val_sr.load(value, ctx)

    def dump_value(self, key, value: Any, ctx: Context) -> Primitive:
        with ctx.enter(CollectionStep(key)):
            return self._val_sr.dump(value, ctx)


class CollectionSerializer(FieldSerializer):
    """Serializer for lists, tuples, sets, frozensets and deques."""

    def __init__(self, field: FieldDescriptor, sr: SeriousSchema):
        super().__init__(field, sr)
        item = generic_item_serializer(field, sr, param_index=0)
        self._load_item = item.load
        self._dump_item = item.dump

    @classmethod
    def fits(cls, field: FieldDescriptor) -> bool:
        type_ = field.type
        return (issubclass(type_.cls, (list, set, frozenset))
                or (issubclass(type_.cls, tuple) and len(type_.parameters) == 2 and type_.parameters[1] is Ellipsis))

    def load(self, value: Primitive, ctx: Context) -> Any:
        items = [self.load_item(i, item, ctx) for i, item in enumerate(value)]  # type: ignore # value is a collection
        return self._field.type.cls(items)

    def dump(self, value: Any, ctx: Context) -> Primitive:
        return [self.dump_item(i, item, ctx) for i, item in enumerate(value)]

    def load_item(self, i: int, value: Primitive, ctx: Context):
        with ctx.enter(CollectionStep(i)):
            return self._load_item(value, ctx)

    def dump_item(self, i: int, value: Any, ctx: Context):
        with ctx.enter(CollectionStep(i)):
            return self._dump_item(value, ctx)


class TupleSerializer(FieldSerializer):
    """Serializer for lists, tuples, sets, frozensets and deques."""

    def __init__(self, field: FieldDescriptor, sr: SeriousSchema):
        super().__init__(field, sr)
        self.serializers: List[FieldSerializer] = []
        for i in field.type.parameters:
            item_serializer = generic_item_serializer(field, sr, param_index=i)
            self.serializers.append(item_serializer)

    @classmethod
    def fits(cls, field: FieldDescriptor) -> bool:
        type_ = field.type
        return issubclass(type_.cls, tuple)

    def load(self, value: Primitive, ctx: Context) -> Any:
        items = [self.load_item(i, item, ctx) for i, item in enumerate(value)]  # type: ignore # value is a collection
        return self._field.type.cls(items)

    def dump(self, value: Any, ctx: Context) -> Primitive:
        return [self.dump_item(i, item, ctx) for i, item in enumerate(value)]

    def load_item(self, i: int, value: Primitive, ctx: Context):
        with ctx.enter(CollectionStep(i)):
            return self.serializers[i].load(value, ctx)

    def dump_item(self, i: int, value: Any, ctx: Context):
        with ctx.enter(CollectionStep(i)):
            return self.serializers[i].dump(value, ctx)


class CollectionStep(SerializationStep):
    def __init__(self, index):
        self.index = index

    def step_name(self) -> str:
        return f'[{self.index}]'


class PrimitiveSerializer(FieldSerializer):
    """A serializer for str, int, float and bool field values."""

    @classmethod
    def fits(cls, field: FieldDescriptor) -> bool:
        return issubclass(field.type.cls, (str, int, float, bool))

    def load(self, value: Primitive, ctx: Context) -> Any:
        return self.field.type.cls(value)

    def dump(self, value: Any, ctx: Context) -> Primitive:
        return self.field.type.cls(value)


class DataclassSerializer(FieldSerializer):
    """A serializer for field values that are dataclasses instances."""

    def __init__(self, field: FieldDescriptor, sr: SeriousSchema):
        super().__init__(field, sr)
        self._serializer = sr.child_serializer(field)

    @classmethod
    def fits(cls, field: FieldDescriptor) -> bool:
        return field.type.is_dataclass

    def load(self, value: Primitive, ctx: Context) -> Any:
        return self._serializer.load(value, ctx)  # type: ignore # type: ignore # value always a mapping

    def dump(self, value: Any, ctx: Context) -> Primitive:
        return self._serializer.dump(value, ctx)


class DateTimeUtcTimestampSerializer(FieldSerializer):
    """A serializer of UTC timestamp field values to/from float value.

    Example:
    ```
    from serious.types import timestamp

    @dataclass
    class Transaction:
        created_at: timestamp

    transaction = Transaction(timestamp(1542473728.456753))
    ```
    Dumping the `post` will return `{"created_at": 1542473728.456753}`.
    """

    @classmethod
    def fits(cls, field: FieldDescriptor) -> bool:
        return issubclass(field.type.cls, Timestamp)

    def load(self, value: Primitive, ctx: Context) -> Any:
        return timestamp(value)  # type: ignore # expecting float

    def dump(self, value: Any, ctx: Context) -> Primitive:
        return value.value


class DateTimeIsoSerializer(FieldSerializer):
    """A serializer for datetime field values to a timestamp represented by a [ISO formatted string][1].

    Example:
    ```
    @dataclass
    class Post:
        timestamp: datetime

    timestamp = datetime(2018, 11, 17, 16, 55, 28, 456753, tzinfo=timezone.utc)
    post = Post(timestamp)
    ```
    Dumping the `post` will return `'{"timestamp": "2018-11-17T16:55:28.456753+00:00"}'`.

    [1]: https://en.wikipedia.org/wiki/ISO_8601
    """

    def load(self, value: Primitive, ctx: Context) -> Any:
        return datetime.fromisoformat(value)  # type: ignore # expecting datetime

    def dump(self, value: Any, ctx: Context) -> Primitive:
        return datetime.isoformat(value)

    @classmethod
    def fits(cls, field: FieldDescriptor) -> bool:
        return issubclass(field.type.cls, datetime)


class DateIsoSerializer(FieldSerializer):
    """A serializer of `date` field values to a timestamp represented by an [ISO formatted string][1].

    Example:
    ```
    @dataclass
    class Event:
        name: str
        when: date

    event = Event('Albert Einstein won Nobel Prize in Physics', date(1922, 9, 9))
    ```
    Dumping the `event` will return `'{"name": "…", "when": "1922-09-09"}'`.

    [1]: https://en.wikipedia.org/wiki/ISO_8601
    """

    def load(self, value: Primitive, ctx: Context) -> Any:
        return date.fromisoformat(value)  # type: ignore # expecting datetime

    def dump(self, value: Any, ctx: Context) -> Primitive:
        return date.isoformat(value)

    @classmethod
    def fits(cls, field: FieldDescriptor) -> bool:
        return issubclass(field.type.cls, date)


class TimeIsoSerializer(FieldSerializer):
    """A serializer for `time` field values to an [ISO formatted string][1].

    Example:
    ```
    @dataclass
    class Alarm:
        at: time
        enabled: bool

    alarm = Alarm(time(7, 0, 0), enabled=True)
    ```
    Dumping the `post` will return `'{"at": "07:00:00", "enabled": True}'`.

    [1]: https://en.wikipedia.org/wiki/ISO_8601
    """

    def load(self, value: Primitive, ctx: Context) -> Any:
        return time.fromisoformat(value)  # type: ignore # expecting datetime

    def dump(self, value: Any, ctx: Context) -> Primitive:
        return time.isoformat(value)

    @classmethod
    def fits(cls, field: FieldDescriptor) -> bool:
        return issubclass(field.type.cls, time)


class UuidSerializer(FieldSerializer):
    """A [UUID] value serializer to `str`."""

    def load(self, value: Primitive, ctx: Context) -> Any:
        return UUID(value)  # type: ignore # expecting str

    def dump(self, value: Any, ctx: Context) -> Primitive:
        return str(value)

    @classmethod
    def fits(cls, field: FieldDescriptor) -> bool:
        return issubclass(field.type.cls, UUID)


class DecimalSerializer(FieldSerializer):
    """[Decimal] value serializer to `str`."""

    def load(self, value: Primitive, ctx: Context) -> Any:
        return Decimal(value)  # type: ignore # expecting str

    def dump(self, value: Any, ctx: Context) -> Primitive:
        return str(value)

    @classmethod
    def fits(cls, field: FieldDescriptor) -> bool:
        return issubclass(field.type.cls, Decimal)


def generic_item_serializer(field: FieldDescriptor, sr: SeriousSchema, *, param_index: int) -> FieldSerializer:
    new_type = field.type.parameters[param_index]
    item_descriptor = replace(field, type=new_type)
    item_serializer = sr.field_serializer(item_descriptor)
    return item_serializer
