from __future__ import annotations

import re
from abc import abstractmethod, ABC
from contextlib import contextmanager
from dataclasses import replace, fields, MISSING, Field
from datetime import datetime, date, time
from decimal import Decimal
from enum import Enum
from typing import Any, Type, Iterable, Optional, Pattern, List, TypeVar, Generic, Dict, Union, Mapping, Iterator, \
    Tuple
from uuid import UUID

from .descriptors import FieldDescriptor, TypeDescriptor, _scan_types
from .errors import ModelContainsAny, ModelContainsUnion, MissingField, UnexpectedItem, LoadError, DumpError, \
    InvalidFieldMetadata, ValidationError
from .preconditions import _check_is_instance, _check_present, _check_is_dataclass
from .types import FrozenList, Timestamp
from .utils import DataclassType, Primitive
from .validation import validate


class Serialization(ABC):

    def __init__(self):
        self._steps: List[SerializationStep] = list()

    @contextmanager
    def _entering(self, step: SerializationStep):
        self._steps.append(step)
        yield
        self._steps.pop()

    @property
    def stack(self) -> FrozenList[SerializationStep]:
        return FrozenList(self._steps)

    @abstractmethod
    def run(self, serializer: Serializer, value: Any) -> Any:
        raise NotImplementedError


class Loading(Serialization):
    def run(self, serializer: Serializer, value: Any) -> Any:
        with self._entering(serializer):
            result = serializer.load(value, self)
            return validate(result)


class Dumping(Serialization):
    def run(self, serializer: Serializer, o: Any) -> Any:
        with self._entering(serializer):
            return serializer.dump(o, self)


class SerializationStep(ABC):

    @abstractmethod
    def step_name(self) -> str:
        raise NotImplementedError


class Serializer(SerializationStep, ABC):

    @abstractmethod
    def load(self, value: Primitive, ctx: Loading) -> Any:
        raise NotImplementedError

    @abstractmethod
    def dump(self, value: Any, ctx: Dumping) -> Primitive:
        raise NotImplementedError


class FieldSerializer(Serializer, ABC):
    """
    A abstract field serializer defining a constructor invoked by serious, [dump](#dump)/[load](#load)
    and class [fits](#fits) methods.

    Field serializers are provided to a serious model ([JsonModel][1], [DictModel][2], [YamlModel][3]) serializers
    parameter in an order in which they will be tested for fitness in.

    A clean way to add custom serializers to the defaults is to use the [field_serializers] function.

    [1]: serious.json.api.JsonModel
    [2]: serious.dict.api.DictModel
    [3]: serious.yaml.api.YamlModel
    """

    def __init__(self, field: FieldDescriptor, root_model: SeriousModel):
        self._field = field
        self._root = root_model
        self._step_name = f'.{field.name}'

    @classmethod
    @abstractmethod
    def fits(cls, field: FieldDescriptor) -> bool:
        """
        A predicate returning `True` if this serializer fits to load/dump data for the provided field.

        The first fitting `FieldSerializer` from the list provided to the model will be used.

        Beware, the `field.type.cls` property can be an instance of a generic alias which will error,
        if using `issubclass` which expects a `type`.
        """
        raise NotImplementedError(f"FieldSerializer {cls} must implement the `#fits(FieldDescriptor)` method.")

    def step_name(self):
        return self._step_name

    @property
    def field(self) -> FieldDescriptor:
        """Read access to the field processed by the serializer."""
        return self._field

    def _generic_item_serializer(self, *, param_index: int) -> FieldSerializer:
        new_type = self.field.type.parameters[param_index]
        item_descriptor = replace(self.field, type=new_type)
        item_serializer = self._root.field_serializer(item_descriptor)
        return item_serializer


def field_serializers(custom: Iterable[Type[FieldSerializer]] = tuple()) -> Tuple[Type[FieldSerializer], ...]:
    """
    Returns a tuple of field serializers in a default order.
    Provide a list of custom field serializers to include them after metadata and optional serializers.
    The order in the collection defines the order in which the serializers will be tested for fitness for each field.
    """
    return tuple([
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

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        metadata = self.field.metadata['serious']
        self._load_method = metadata['load']
        self._dump_method = metadata['dump']

    def load(self, value: Primitive, ctx: Loading) -> Any:
        return self._load_method(value, ctx)

    def dump(self, value: Any, ctx: Dumping) -> Primitive:
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

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        item_descriptor = replace(self.field, type=replace(self.field.type, is_optional=False))
        self._serializer = self._root.field_serializer(item_descriptor)

    def load(self, value: Primitive, ctx: Loading) -> Any:
        return None if value is None else self._serializer.load(value, ctx)

    def dump(self, value: Any, ctx: Dumping) -> Primitive:
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

    model = DictModel(HistoricEvent)
    dict = {'name': name, 'date': '1961-04-11'}
    dataclass = HistoricEvent(name, Date.GAGARIN)
    assert model.load(dict) == dataclass  # True
    ```"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
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

    def load(self, value: Primitive, ctx: Loading) -> Any:
        if self._serializer is None and value not in self._enum_values:
            raise ValidationError(f'"{value}" is not part of the {self.field.type.cls} enum')
        enum_cls = self.field.type.cls
        if self._serializer is not None:
            loaded_value = self._serializer.load(value, ctx)
            try:
                return enum_cls(loaded_value)
            except ValueError as e:
                raise ValidationError(f'"{value}" is not part of the {enum_cls} enum') from e
        return enum_cls(value)

    def dump(self, value: Any, ctx: Dumping) -> Primitive:
        enum_value = value.value
        if self._serializer is not None:
            return self._serializer.dump(enum_value, ctx)
        return enum_value

    @classmethod
    def fits(cls, field: FieldDescriptor) -> bool:
        return issubclass(field.type.cls, Enum)


class AnySerializer(FieldSerializer):
    """Serializer for [Any] fields."""

    def load(self, value: Primitive, ctx: Loading) -> Any:
        return value

    def dump(self, value: Any, ctx: Dumping) -> Primitive:
        return value

    @classmethod
    def fits(cls, field: FieldDescriptor) -> bool:
        return field.type.cls is Any


class DictSerializer(FieldSerializer):
    """Serializer for `dict` fields with `str` keys (Dict[str, Any])."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        key = self.field.type.parameters[0]
        assert key.cls is str and not key.is_optional, 'Dict keys must have explicit "str" type (Dict[str, Any]).'
        self._serializer = self._generic_item_serializer(param_index=1)

    @classmethod
    def fits(cls, field: FieldDescriptor) -> bool:
        return issubclass(field.type.cls, dict)

    def load(self, data: Primitive, ctx: Loading) -> Any:
        if not isinstance(data, dict):
            raise ValidationError('Expecting a dictionary')
        items = self._serialize_dict(data, ctx)
        return self.field.type.cls(items)

    def dump(self, data: Any, ctx: Dumping) -> Primitive:
        return self._serialize_dict(data, ctx)

    def _serialize_dict(self, data: Any, ctx: Serialization) -> Dict[str, Any]:
        serializer = Alias(self._serializer)
        return {key: ctx.run(serializer(key), value) for key, value in data.items()}


class CollectionSerializer(FieldSerializer):
    """Serializer for lists, sets, and frozensets."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._serializer = self._generic_item_serializer(param_index=0)
        self._item_type = self._serializer.field.type

    @classmethod
    def fits(cls, field: FieldDescriptor) -> bool:
        type_ = field.type
        return (issubclass(type_.cls, (list, set, frozenset))
                or (issubclass(type_.cls, tuple)
                    and len(type_.parameters) == 2
                    and type_.parameters[1] is Ellipsis))

    def load(self, value: Primitive, ctx: Loading) -> Any:
        if not isinstance(value, list):
            raise ValidationError(f'Expecting a list of {self._item_type.cls} values')
        items = self._serialize_collection(value, ctx)
        return self.field.type.cls(items)

    def dump(self, value: Any, ctx: Dumping) -> Primitive:
        return self._serialize_collection(value, ctx)

    def _serialize_collection(self, data: Any, ctx: Serialization) -> List[Any]:
        serializer = Alias(self._serializer)
        return [ctx.run(serializer(i), item) for i, item in enumerate(data)]


class TupleSerializer(FieldSerializer):
    """Serializer for Python tuples."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._serializers = [self._generic_item_serializer(param_index=i) for i in self.field.type.parameters]
        self._size = len(self._serializers)

    @classmethod
    def fits(cls, field: FieldDescriptor) -> bool:
        return issubclass(field.type.cls, tuple)

    def load(self, value: Primitive, ctx: Loading) -> Any:
        if not isinstance(value, list):
            raise ValidationError(f'Expecting a list of {self._size} tuple values')
        if len(value) != self._size:
            raise ValidationError(f'Expecting a list of {self._size} tuple values')  # type: ignore
        items = self._serialize_tuple(value, ctx)
        return self.field.type.cls(items)

    def dump(self, value: Any, ctx: Dumping) -> Primitive:
        return self._serialize_tuple(value, ctx)

    def _serialize_tuple(self, data: Any, ctx: Serialization) -> List[Any]:
        serializer = OrdinalAlias(self._serializers)
        return [ctx.run(serializer(i), item) for i, item in enumerate(data)]


class Alias(Serializer):
    """Serializes values using the constructor parameter, but step name via calling instance as a function."""

    def __init__(self, serializer):
        self._serializer = serializer

    def __call__(self, key: Union[str, int]) -> Alias:
        self._key = key
        return self

    def step_name(self) -> str:
        return f'[{self._key}]'

    def load(self, value: Primitive, ctx: Loading) -> Any:
        return self._serializer.load(value, ctx)

    def dump(self, value: Any, ctx: Dumping) -> Primitive:
        return self._serializer.dump(value, ctx)


class OrdinalAlias(Serializer):
    """Serializes values using the provided serializer at the currently set index.
    The index is set via calling instance as a function.
    Step name is changed to match the index."""

    def __init__(self, serializers: List[Serializer]):
        self._serializers = serializers

    def __call__(self, index: int) -> OrdinalAlias:
        self._index = index
        return self

    def step_name(self) -> str:
        return f'[{self._index}]'

    def load(self, value: Primitive, ctx: Loading) -> Any:
        return self._serializers[self._index].load(value, ctx)

    def dump(self, value: Any, ctx: Dumping) -> Primitive:
        return self._serializers[self._index].dump(value, ctx)


class BooleanSerializer(FieldSerializer):
    """A serializer boolean field values."""

    @classmethod
    def fits(cls, field: FieldDescriptor) -> bool:
        return issubclass(field.type.cls, bool)

    def load(self, value: Primitive, ctx: Loading) -> Any:
        if not isinstance(value, bool):
            raise ValidationError(f"Invalid data type. Expecting boolean")
        return self.field.type.cls(value)

    def dump(self, value: Any, ctx: Dumping) -> Primitive:
        return bool(value)


class StringSerializer(FieldSerializer):
    """A serializer for string field values."""

    @classmethod
    def fits(cls, field: FieldDescriptor) -> bool:
        return issubclass(field.type.cls, str)

    def load(self, value: Primitive, ctx: Loading) -> Any:
        if not isinstance(value, str):
            raise ValidationError('Invalid data type. Expecting a string')
        return self.field.type.cls(value)

    def dump(self, value: Any, ctx: Dumping) -> Primitive:
        return str(value)


class IntegerSerializer(FieldSerializer):
    """A serializer for integer field values.

    In Python bool is a subclass of int, thus the check."""

    @classmethod
    def fits(cls, field: FieldDescriptor) -> bool:
        type_ = field.type.cls
        return issubclass(type_, int) and not issubclass(type_, bool)

    def load(self, value: Primitive, ctx: Loading) -> Any:
        if not isinstance(value, int) or isinstance(value, bool):
            raise ValidationError('Invalid data type. Expecting an integer')
        return self.field.type.cls(value)

    def dump(self, value: Any, ctx: Dumping) -> Primitive:
        return int(value)


class FloatSerializer(FieldSerializer):
    """A serializer for float values field values.

    During load this can be either an int (1) or float (1.0). Always dumps to float."""

    @classmethod
    def fits(cls, field: FieldDescriptor) -> bool:
        type_ = field.type.cls
        return issubclass(type_, float)

    def load(self, value: Primitive, ctx: Loading) -> Any:
        is_numeric = isinstance(value, (int, float)) and not isinstance(value, bool)
        if not is_numeric:
            raise ValidationError('Invalid data type. Expecting a numeric value')
        return self.field.type.cls(value)

    def dump(self, value: Any, ctx: Dumping) -> Primitive:
        return float(value)


class DataclassSerializer(FieldSerializer):
    """A serializer for field values that are dataclasses instances."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._serializer = self._root.child_model(self.field)
        self._dc_name = self.field.type.cls.__name__

    @classmethod
    def fits(cls, field: FieldDescriptor) -> bool:
        return field.type.is_dataclass

    def load(self, value: Primitive, ctx: Loading) -> Any:
        if not isinstance(value, dict):
            raise ValidationError(f'Invalid data type. Expecting a mapping matching {self._dc_name} model')
        return self._serializer.load(value, ctx)  # type: ignore # type: ignore # value always a mapping

    def dump(self, value: Any, ctx: Dumping) -> Primitive:
        return self._serializer.dump(value, ctx)


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

    def load(self, value: Primitive, ctx: Loading) -> Any:
        if not isinstance(value, (int, float)):
            raise ValidationError('Invalid data type. Expecting int or float')
        return Timestamp(value)  # type: ignore # expecting float

    def dump(self, value: Any, ctx: Dumping) -> Primitive:
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

    def load(self, value: Primitive, ctx: Loading) -> Any:
        if not isinstance(value, str):
            raise ValidationError('Invalid data type. Expecting a string')
        if not _matches(_iso_date_time_re, value):
            raise ValidationError('Invalid date/time format. Check the ISO 8601 specification')
        return datetime.fromisoformat(value)  # type: ignore # expecting datetime

    def dump(self, value: Any, ctx: Dumping) -> Primitive:
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

    def load(self, value: Primitive, ctx: Loading) -> Any:
        if not isinstance(value, str):
            raise ValidationError('Invalid data type. Expecting a string')
        if not _matches(_iso_date_re, value):
            raise ValidationError('Invalid date format. Check the ISO 8601 specification')
        return date.fromisoformat(value)  # type: ignore # expecting datetime

    def dump(self, value: Any, ctx: Dumping) -> Primitive:
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

    def load(self, value: Primitive, ctx: Loading) -> Any:
        if not isinstance(value, str):
            raise ValidationError('Invalid data type. Expecting a string')
        if not _matches(_iso_time_re, value):
            raise ValidationError('Invalid time format. Check the ISO 8601 specification')
        return time.fromisoformat(value)  # type: ignore # expecting datetime

    def dump(self, value: Any, ctx: Dumping) -> Primitive:
        return time.isoformat(value)

    @classmethod
    def fits(cls, field: FieldDescriptor) -> bool:
        return issubclass(field.type.cls, time)


_uuid4_hex_re = re.compile(r'\A([a-f0-9]{8}-?[a-f0-9]{4}-?4[a-f0-9]{3}-?[89ab][a-f0-9]{3}-?[a-f0-9]{12})\Z', re.I)


class UuidSerializer(FieldSerializer):
    """A [UUID] value serializer to `str`."""

    def load(self, value: Primitive, ctx: Loading) -> Any:
        if not isinstance(value, str):
            raise ValidationError('Invalid data type. Expecting a string')
        if not _matches(_uuid4_hex_re, value):
            raise ValidationError('Invalid UUID4 hex format')
        return UUID(value)  # type: ignore # expecting str

    def dump(self, value: Any, ctx: Dumping) -> Primitive:
        return str(value)

    @classmethod
    def fits(cls, field: FieldDescriptor) -> bool:
        return issubclass(field.type.cls, UUID)


_decimal_re = re.compile(r'\A\d+?\.\d+?\Z')


class DecimalSerializer(FieldSerializer):
    """[Decimal] value serializer to `str`."""

    def load(self, value: Primitive, ctx: Loading) -> Any:
        if not isinstance(value, str):
            raise ValidationError('Invalid data type. Expecting a string')
        if not _matches(_decimal_re, value):
            raise ValidationError('Invalid decimal format. A number with a "." as a decimal separator is expected')
        return Decimal(value)  # type: ignore # expecting str

    def dump(self, value: Any, ctx: Dumping) -> Primitive:
        return str(value)

    @classmethod
    def fits(cls, field: FieldDescriptor) -> bool:
        return issubclass(field.type.cls, Decimal)


T = TypeVar('T')


class SeriousModel(Generic[T]):
    """A serializer for dataclasses from and to a dict."""

    def __init__(
            self,
            descriptor: TypeDescriptor,
            serializers: Iterable[Type[FieldSerializer]],
            *,
            allow_any: bool,
            allow_missing: bool,
            allow_unexpected: bool,
            _registry: Dict[TypeDescriptor, SeriousModel] = None
    ):
        """
        @param descriptor the descriptor of the dataclass to load/dump.
        @param serializers field serializer classes in an order they will be tested for fitness for each field.
        @param allow_any `False` to raise if the model contains fields annotated with `Any`
                (this includes generics like `List[Any]`, or simply `list`).
        @param allow_missing `False` to raise during load if data is missing the optional fields.
        @param allow_unexpected `False` to raise during load if data contains some unknown fields.
        @param _registry a mapping of dataclass type descriptors to corresponding serious serializer;
                used internally to create child serializers.
        """
        _check_is_dataclass(descriptor.cls, 'Serious can only operate on dataclasses.')
        all_types = _scan_types(descriptor)
        if not allow_any and Any in all_types:
            raise ModelContainsAny(descriptor.cls)
        if Union in all_types:
            raise ModelContainsUnion(descriptor.cls)
        self._descriptor = descriptor
        self._serializers = tuple(serializers)
        self._allow_missing = allow_missing
        self._allow_unexpected = allow_unexpected
        self._allow_any = allow_any
        self._serializer_registry = {descriptor: self} if _registry is None else _registry
        self._field_serializers = [self.field_serializer(field) for field in descriptor.fields]

    @property
    def _cls(self) -> Type[T]:
        # A shortcut to root dataclass type.
        return self._descriptor.cls

    def child_model(self, field: FieldDescriptor) -> SeriousModel:
        """
        Creates a [SeriousModel] for dataclass fields nested in the current serializers.
        The preferences of the nested dataclasses match those of the root one.
        """

        descriptor = field.type
        if descriptor in self._serializer_registry:
            return self._serializer_registry[descriptor]
        new_model: SeriousModel = SeriousModel(
            descriptor=descriptor,
            serializers=self._serializers,
            allow_missing=self._allow_missing,
            allow_unexpected=self._allow_unexpected,
            allow_any=self._allow_any,
            _registry=self._serializer_registry
        )
        self._serializer_registry[descriptor] = new_model
        return new_model

    def load(self, data: Mapping, _ctx: Optional[Loading] = None) -> T:
        """Loads dataclass from a dictionary or other mapping. """

        _check_is_instance(data, Mapping, f'Invalid data for {self._cls}')  # type: ignore
        root = _ctx is None
        loading: Loading = Loading() if root else _ctx  # type: ignore # checked above
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
                field: loading.run(serializer, mut_data[field])
                for field, serializer in _named(self._field_serializers)
                if field in mut_data
            }
            result = self._cls(**init_kwargs)  # type: ignore # not an object
            validate(result)
            return result
        except Exception as e:
            if root:
                if isinstance(e, ValidationError):
                    raise
                else:
                    raise LoadError(self._cls, loading.stack, data) from e
            raise

    def dump(self, o: T, _ctx: Optional[Dumping] = None) -> Dict[str, Any]:
        """Dumps a dataclass object to a dictionary."""

        _check_is_instance(o, self._cls)
        root = _ctx is None
        dumping: Dumping = Dumping() if root else _ctx  # type: ignore # checked above
        try:
            return {
                field: dumping.run(serializer, getattr(o, field))
                for field, serializer in _named(self._field_serializers)
            }
        except Exception as e:
            if root:
                raise DumpError(o, dumping.stack) from e
            raise

    def field_serializer(self, field: FieldDescriptor) -> FieldSerializer:
        """
        Creates a serializer fitting the provided field descriptor.

        @param field descriptor of a field to serialize.
        """
        optional = self._get_serializer(field)
        serializer = _check_present(optional, f'Type "{field.type.cls}" is not supported')
        return serializer

    def _get_serializer(self, field: FieldDescriptor) -> Optional[FieldSerializer]:
        sr_generator = (serializer(field, self) for serializer in self._serializers if serializer.fits(field))
        optional_sr = next(sr_generator, None)
        return optional_sr


def _named(serializers: List[FieldSerializer]) -> Iterator[Tuple[str, FieldSerializer]]:
    return ((s.field.name, s) for s in serializers)


def _check_for_missing(cls: DataclassType, data: Mapping) -> None:
    """
    Checks for missing keys in data that are part of the provided dataclass.

    @raises MissingField
    """
    missing_fields = filter(lambda f: f.name not in data, fields(cls))
    first_missing_field: Any = next(missing_fields, MISSING)
    if first_missing_field is not MISSING:
        field_names = {first_missing_field.name} | {field.name for field in missing_fields}
        raise MissingField(cls, data, field_names)


def _check_for_unexpected(cls: DataclassType, data: Mapping) -> None:
    """
    Checks for keys in data that are not part of the provided dataclass.

    @raises UnexpectedItem
    """
    field_names = {field.name for field in fields(cls)}
    data_keys = set(data.keys())
    unexpected_fields = data_keys - field_names
    if any(unexpected_fields):
        raise UnexpectedItem(cls, data, unexpected_fields)


def _fields_missing_from(data: Mapping, cls: DataclassType) -> Iterator[Field]:
    """Fields missing from data, but present in the dataclass."""

    def _is_missing(field: Field) -> bool:
        return field.name not in data \
               and field.default is MISSING \
               and field.default_factory is MISSING  # type: ignore # default factory is an unbound function

    return filter(_is_missing, fields(cls))


def _matches(regex: Pattern, value: Primitive) -> bool:
    return regex.match(value) is not None  # type: ignore # caller ensures str
