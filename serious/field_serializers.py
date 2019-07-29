from __future__ import annotations

import re
from abc import abstractmethod, ABC
from dataclasses import replace
from datetime import datetime, date, time
from decimal import Decimal
from enum import Enum
from typing import Any, Type, Iterable, Optional, Pattern
from uuid import UUID

from serious.context import SerializationContext as Context, SerializationStep
from serious.descriptors import FieldDescriptor
from serious.errors import InvalidFieldMetadata, ValidationError
from serious.types import FrozenList, FrozenList, Timestamp, Timestamp
from serious.utils import Primitive
from serious.validation import validate, validate_object

if False:  # To reference in typings
    from serious.schema import SeriousSchema


def _matches(regex: Pattern, value: Primitive) -> bool:
    return regex.match(value) is not None  # type: ignore # caller ensures str


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

    def __init__(self, field: FieldDescriptor, root_serializer: SeriousSchema):
        self._field = field
        self._root = root_serializer

    @classmethod
    @abstractmethod
    def fits(cls, field: FieldDescriptor) -> bool:
        """
        A predicate returning `True` if this serializer fits to load/dump data for the provided field.

        The first fitting `FieldSerializer` from the list provided to the schema will be used.

        Beware, the `field.type.cls` property can be an instance of a generic alias which will error,
        if using `issubclass` which expects a `type`.
        """
        raise NotImplementedError(f"Serializer {cls} must implement the `#fits(FieldDescriptor)` method.")

    def step_name(self):
        return f'.{self.field.name}'

    @property
    def field(self) -> FieldDescriptor:
        """Read access to the field processed by the serializer."""
        return self._field

    def load(self, value: Primitive, ctx: Context) -> Any:
        self._validate_data(value, ctx)
        result = self._load(value, ctx)
        validate_object(result)
        return result

    def dump(self, value: Any, ctx: Context) -> Primitive:
        return self._dump(value, ctx)

    @abstractmethod
    def _load(self, value: Primitive, ctx: Context) -> Any:
        raise NotImplementedError

    @abstractmethod
    def _dump(self, value: Any, ctx: Context) -> Primitive:
        raise NotImplementedError

    def _validate_data(self, value: Primitive, ctx: Context) -> None:
        """Override to validate data on load."""
        pass

    def _generic_item_serializer(self, *, param_index: int) -> FieldSerializer:
        new_type = self.field.type.parameters[param_index]
        item_descriptor = replace(self.field, type=new_type)
        item_serializer = self._root.field_serializer(item_descriptor)
        return item_serializer


def field_serializers(custom: Iterable[Type[FieldSerializer]] = tuple()) -> FrozenList[Type[FieldSerializer]]:
    """
    A tuple of field serializers in a default order.
    Provide a custom list of field serializers to include them after metadata and optional serializers.
    The order in the collection defines the order in which the serializers will be tested for fitness for each field.
    """
    return FrozenList([
        MetadataSerializer,
        OptionalSerializer,
        AnySerializer,
        EnumSerializer,
        *custom,
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

    def __init__(self, field: FieldDescriptor, root_serializer: SeriousSchema):
        super().__init__(field, root_serializer)
        metadata = field.metadata['serious']
        self._load_method = metadata['load']
        self._dump_method = metadata['dump']

    def _load(self, value: Primitive, ctx: Context) -> Any:
        return self._load_method(value, ctx)

    def _dump(self, value: Any, ctx: Context) -> Primitive:
        return self._dump_method(value, ctx)

    @classmethod
    def fits(cls, field: FieldDescriptor) -> bool:
        metadata = field.metadata
        if 'serious' not in metadata:
            return False
        contains_load = 'load' in metadata['serious']
        contains_dump = 'dump' in metadata['serious']
        if not contains_dump and not contains_load:
            return False
        if (contains_load and not contains_dump) or (contains_dump and not contains_load):
            error = 'Both "load" and "dump" must be present in serious metadata to use it for serialization.'
            raise InvalidFieldMetadata(field, error)
        return True


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

    def __init__(self, field: FieldDescriptor, root_serializer: SeriousSchema):
        super().__init__(field, root_serializer)
        item_descriptor = replace(field, type=replace(field.type, is_optional=False))
        self._serializer = self._root.field_serializer(item_descriptor)

    def _load(self, value: Primitive, ctx: Context) -> Any:
        return None if value is None else self._serializer.load(value, ctx)

    def _dump(self, value: Any, ctx: Context) -> Primitive:
        return None if value is None else self._serializer.dump(value, ctx)

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

    def __init__(self, field: FieldDescriptor, root_serializer: SeriousSchema):
        super().__init__(field, root_serializer)
        self._serializer = self._value_serializer()
        self._enum_values = {e.value for e in list(self.field.type.cls)}

    def _value_serializer(self) -> Optional[FieldSerializer]:
        cls = self.field.type.cls
        bases = cls.__bases__
        while len(bases) == 1:
            cls = bases[0]
            bases = cls.__bases__
        if len(bases) == 0:
            return None
        item_descriptor = replace(self.field, type=self.field.type.describe(bases[0]))
        return self._root.field_serializer(item_descriptor)

    def _load(self, value: Primitive, ctx: Context) -> Any:
        enum_cls = self.field.type.cls
        if self._serializer is not None:
            loaded_value = self._serializer.load(value, ctx)
            try:
                return enum_cls(loaded_value)
            except ValueError as e:
                raise ValidationError(f'"{value}" is not part of the {enum_cls} enum') from e
        return enum_cls(value)

    def _validate_data(self, data: Primitive, ctx: Context) -> None:
        if self._serializer is None:
            validate(data in self._enum_values, f'"{data}" is not part of the {self.field.type.cls} enum')

    def _dump(self, value: Any, ctx: Context) -> Primitive:
        enum_value = value.value
        if self._serializer is not None:
            return self._serializer.dump(enum_value, ctx)
        return enum_value

    @classmethod
    def fits(cls, field: FieldDescriptor) -> bool:
        return issubclass(field.type.cls, Enum)


class AnySerializer(FieldSerializer):
    """Serializer for [Any] fields."""

    def _load(self, value: Primitive, ctx: Context) -> Any:
        return value

    def _dump(self, value: Any, ctx: Context) -> Primitive:
        return value

    @classmethod
    def fits(cls, field: FieldDescriptor) -> bool:
        return field.type.cls is Any


class DictSerializer(FieldSerializer):
    """Serializer for `dict` fields with `str` keys (Dict[str, Any])."""

    def __init__(self, field: FieldDescriptor, root_serializer: SeriousSchema):
        super().__init__(field, root_serializer)
        key = field.type.parameters[0]
        assert key.cls is str and not key.is_optional, 'Dict keys must have explicit "str" type (Dict[str, Any]).'
        self._val_sr = self._generic_item_serializer(param_index=1)

    @classmethod
    def fits(cls, field: FieldDescriptor) -> bool:
        return issubclass(field.type.cls, dict)

    def _load(self, data: Primitive, ctx: Context) -> Any:
        items = {
            key: self.load_value(key, value, ctx)
            for key, value in data.items()  # type: ignore # data is always a dict
        }
        return self.field.type.cls(items)

    def _dump(self, d: Any, ctx: Context) -> Primitive:
        return {key: self.dump_value(key, value, ctx) for key, value in d.items()}

    def load_value(self, key, value: Primitive, ctx: Context) -> Any:
        with ctx.enter(CollectionStep(key)):
            return self._val_sr.load(value, ctx)

    def dump_value(self, key, value: Any, ctx: Context) -> Primitive:
        with ctx.enter(CollectionStep(key)):
            return self._val_sr.dump(value, ctx)

    def _validate_data(self, value: Primitive, ctx: Context) -> None:
        validate(isinstance(value, dict), f'Expecting a dictionary')


class CollectionSerializer(FieldSerializer):
    """Serializer for lists, sets, and frozensets."""

    def __init__(self, field: FieldDescriptor, root_serializer: SeriousSchema):
        super().__init__(field, root_serializer)
        item = self._generic_item_serializer(param_index=0)
        self._item_type = item.field.type
        self._load_item = item.load
        self._dump_item = item.dump

    @classmethod
    def fits(cls, field: FieldDescriptor) -> bool:
        type_ = field.type
        return (issubclass(type_.cls, (list, set, frozenset))
                or (issubclass(type_.cls, tuple)
                    and len(type_.parameters) == 2
                    and type_.parameters[1] is Ellipsis))

    def _load(self, value: Primitive, ctx: Context) -> Any:
        items = [self.load_item(i, item, ctx) for i, item in enumerate(value)]  # type: ignore # value is a collection
        return self.field.type.cls(items)

    def _dump(self, value: Any, ctx: Context) -> Primitive:
        return [self.dump_item(i, item, ctx) for i, item in enumerate(value)]

    def load_item(self, i: int, value: Primitive, ctx: Context):
        with ctx.enter(CollectionStep(i)):
            return self._load_item(value, ctx)

    def dump_item(self, i: int, value: Any, ctx: Context):
        with ctx.enter(CollectionStep(i)):
            return self._dump_item(value, ctx)

    def _validate_data(self, value: Primitive, ctx: Context) -> None:
        validate(isinstance(value, list), f'Expecting a list of {self._item_type.cls} values')


class TupleSerializer(FieldSerializer):
    """Serializer for Python tuples."""

    def __init__(self, field: FieldDescriptor, root_serializer: SeriousSchema):
        super().__init__(field, root_serializer)
        self._serializers = [self._generic_item_serializer(param_index=i) for i in self.field.type.parameters]
        self._size = len(self._serializers)

    @classmethod
    def fits(cls, field: FieldDescriptor) -> bool:
        return issubclass(field.type.cls, tuple)

    def _load(self, value: Primitive, ctx: Context) -> Any:
        items = [self.load_item(i, item, ctx) for i, item in enumerate(value)]  # type: ignore # value is a collection
        return self.field.type.cls(items)

    def _dump(self, value: Any, ctx: Context) -> Primitive:
        return [self.dump_item(i, item, ctx) for i, item in enumerate(value)]

    def load_item(self, i: int, value: Primitive, ctx: Context):
        with ctx.enter(CollectionStep(i)):
            return self._serializers[i].load(value, ctx)

    def dump_item(self, i: int, value: Any, ctx: Context):
        with ctx.enter(CollectionStep(i)):
            return self._serializers[i].dump(value, ctx)

    def _validate_data(self, value: Primitive, ctx: Context) -> None:
        validate(isinstance(value, list), f'Expecting a list of {self._size} tuple values')
        validate(len(value) == self._size, f'Expecting a list of {self._size} tuple values')  # type: ignore


class CollectionStep(SerializationStep):
    # TODO:mdrachuk:2019-07-24: do not create new instance for each item

    def __init__(self, index: int):
        self.index = index

    def step_name(self) -> str:
        return f'[{self.index}]'


class BooleanSerializer(FieldSerializer):
    """A serializer boolean field values."""

    @classmethod
    def fits(cls, field: FieldDescriptor) -> bool:
        return issubclass(field.type.cls, bool)

    def _load(self, value: Primitive, ctx: Context) -> Any:
        return self.field.type.cls(value)

    def _dump(self, value: Any, ctx: Context) -> Primitive:
        return bool(value)

    def _validate_data(self, value: Primitive, ctx: Context) -> None:
        validate(isinstance(value, bool), f'Invalid data type. Expecting boolean')


class StringSerializer(FieldSerializer):
    """A serializer for string field values."""

    @classmethod
    def fits(cls, field: FieldDescriptor) -> bool:
        return issubclass(field.type.cls, str)

    def _load(self, value: Primitive, ctx: Context) -> Any:
        return self.field.type.cls(value)

    def _dump(self, value: Any, ctx: Context) -> Primitive:
        return str(value)

    def _validate_data(self, value: Primitive, ctx: Context) -> None:
        validate(isinstance(value, str), 'Invalid data type. Expecting a string')


class IntegerSerializer(FieldSerializer):
    """A serializer for integer field values.

    In Python bool is a subclass of int, thus the check."""

    @classmethod
    def fits(cls, field: FieldDescriptor) -> bool:
        type_ = field.type.cls
        return issubclass(type_, int) and not issubclass(type_, bool)

    def _load(self, value: Primitive, ctx: Context) -> Any:
        return self.field.type.cls(value)

    def _dump(self, value: Any, ctx: Context) -> Primitive:
        return int(value)

    def _validate_data(self, value: Primitive, ctx: Context) -> None:
        validate(isinstance(value, int) and not isinstance(value, bool), 'Invalid data type. Expecting an integer')


class FloatSerializer(FieldSerializer):
    """A serializer for float values field values.

    During load this can be either an int (1) or float (1.0). Always dumps to float."""

    @classmethod
    def fits(cls, field: FieldDescriptor) -> bool:
        type_ = field.type.cls
        return issubclass(type_, float)

    def _load(self, value: Primitive, ctx: Context) -> Any:
        return self.field.type.cls(value)

    def _dump(self, value: Any, ctx: Context) -> Primitive:
        return float(value)

    def _validate_data(self, value: Primitive, ctx: Context) -> None:
        is_numeric = isinstance(value, (int, float)) and not isinstance(value, bool)
        validate(is_numeric, 'Invalid data type. Expecting a numeric value')


class DataclassSerializer(FieldSerializer):
    """A serializer for field values that are dataclasses instances."""

    def __init__(self, field: FieldDescriptor, root_serializer: SeriousSchema):
        super().__init__(field, root_serializer)
        self._serializer = self._root.child_serializer(field)
        self._dc_name = self.field.type.cls.__name__

    @classmethod
    def fits(cls, field: FieldDescriptor) -> bool:
        return field.type.is_dataclass

    def _load(self, value: Primitive, ctx: Context) -> Any:
        return self._serializer.load(value, ctx)  # type: ignore # type: ignore # value always a mapping

    def _dump(self, value: Any, ctx: Context) -> Primitive:
        return self._serializer.dump(value, ctx)

    def _validate_data(self, value: Primitive, ctx: Context) -> None:
        validate(isinstance(value, dict), f'Invalid data type. Expecting a mapping matching {self._dc_name} schema')


class UtcTimestampSerializer(FieldSerializer):
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

    def _load(self, value: Primitive, ctx: Context) -> Any:
        return Timestamp(value)  # type: ignore # expecting float

    def _dump(self, value: Any, ctx: Context) -> Primitive:
        return value.value

    def _validate_data(self, value: Primitive, ctx: Context) -> None:
        validate(isinstance(value, (int, float)), f'Invalid data type. Expecting int or float')


_iso_date_time_re = re.compile(  # https://stackoverflow.com/a/43931246/8677389
    r'\A(?:[1-9]\d{3}-(?:(?:0[1-9]|1[0-2])-(?:0[1-9]|1\d|2[0-8])|(?:0[13-9]|1[0-2])-(?:29|30)|(?:0[13578]|1[02])-31)|(?:[1-9]\d(?:0[48]|[2468][048]|[13579][26])|(?:[2468][048]|[13579][26])00)-02-29)T(?:[01]\d|2[0-3]):[0-5]\d:[0-5]\d(?:\.\d{1,9})?(?:Z|[+-][01]\d:[0-5]\d)\Z')
_iso_date_re = re.compile(
    r'\A(?P<year>[0-9]{4})(?P<hyphen>-?)(?P<month>1[0-2]|0[1-9])(?P=hyphen)(?P<day>3[01]|0[1-9]|[12][0-9])\Z')
_iso_time_re = re.compile(
    r'\A(?P<hour>2[0-3]|[01][0-9]):?(?P<minute>[0-5][0-9]):?(?P<second>[0-5][0-9])(?P<timezone>Z|[+-](?:2[0-3]|[01][0-9])(?::?(?:[0-5][0-9]))?)?\Z')


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

    def _load(self, value: Primitive, ctx: Context) -> Any:
        return datetime.fromisoformat(value)  # type: ignore # expecting datetime

    def _dump(self, value: Any, ctx: Context) -> Primitive:
        return datetime.isoformat(value)

    @classmethod
    def fits(cls, field: FieldDescriptor) -> bool:
        return issubclass(field.type.cls, datetime)

    def _validate_data(self, value: Primitive, ctx: Context) -> None:
        validate(isinstance(value, str), 'Invalid data type. Expecting a string')
        validate(_matches(_iso_date_time_re, value), 'Invalid date/time format. Check the ISO 8601 specification')


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

    def _load(self, value: Primitive, ctx: Context) -> Any:
        return date.fromisoformat(value)  # type: ignore # expecting datetime

    def _dump(self, value: Any, ctx: Context) -> Primitive:
        return date.isoformat(value)

    @classmethod
    def fits(cls, field: FieldDescriptor) -> bool:
        return issubclass(field.type.cls, date)

    def _validate_data(self, value: Primitive, ctx: Context) -> None:
        validate(isinstance(value, str), 'Invalid data type. Expecting a string')
        validate(_matches(_iso_date_re, value), 'Invalid date format. Check the ISO 8601 specification')


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

    def _load(self, value: Primitive, ctx: Context) -> Any:
        return time.fromisoformat(value)  # type: ignore # expecting datetime

    def _dump(self, value: Any, ctx: Context) -> Primitive:
        return time.isoformat(value)

    @classmethod
    def fits(cls, field: FieldDescriptor) -> bool:
        return issubclass(field.type.cls, time)

    def _validate_data(self, value: Primitive, ctx: Context) -> None:
        validate(isinstance(value, str), 'Invalid data type. Expecting a string')
        validate(_matches(_iso_time_re, value), 'Invalid time format. Check the ISO 8601 specification')


_uuid4_hex_re = re.compile(r'\A([a-f0-9]{8}-?[a-f0-9]{4}-?4[a-f0-9]{3}-?[89ab][a-f0-9]{3}-?[a-f0-9]{12})\Z', re.I)


class UuidSerializer(FieldSerializer):
    """A [UUID] value serializer to `str`."""

    def _load(self, value: Primitive, ctx: Context) -> Any:
        return UUID(value)  # type: ignore # expecting str

    def _dump(self, value: Any, ctx: Context) -> Primitive:
        return str(value)

    @classmethod
    def fits(cls, field: FieldDescriptor) -> bool:
        return issubclass(field.type.cls, UUID)

    def _validate_data(self, value: Primitive, ctx: Context) -> None:
        validate(isinstance(value, str), 'Invalid data type. Expecting a string')
        validate(_matches(_uuid4_hex_re, value), 'Invalid UUID4 hex format')


_decimal_re = re.compile(r'\A\d+?\.\d+?\Z')


class DecimalSerializer(FieldSerializer):
    """[Decimal] value serializer to `str`."""

    def _load(self, value: Primitive, ctx: Context) -> Any:
        return Decimal(value)  # type: ignore # expecting str

    def _dump(self, value: Any, ctx: Context) -> Primitive:
        return str(value)

    @classmethod
    def fits(cls, field: FieldDescriptor) -> bool:
        return issubclass(field.type.cls, Decimal)

    def _validate_data(self, value: Primitive, ctx: Context) -> None:
        validate(isinstance(value, str), 'Invalid data type. Expecting a string')
        validate(_matches(_decimal_re, value),
                 'Invalid decimal format. A number with a "." as a decimal separator is expected')
