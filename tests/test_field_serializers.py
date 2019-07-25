from dataclasses import dataclass
from datetime import date, datetime, timezone, time
from decimal import Decimal
from enum import Enum
from typing import Type, Dict, Any, List, Tuple, Optional
from uuid import UUID

import pytest

from serious import DictSchema
from serious.context import SerializationContext
from serious.descriptors import FieldDescriptor, describe
from serious.errors import ValidationError
from serious.field_serializers import FieldSerializer, BooleanSerializer, StringSerializer, FloatSerializer, \
    IntegerSerializer, EnumSerializer, DictSerializer, AnySerializer, CollectionSerializer, TupleSerializer, \
    DataclassSerializer, UtcTimestampSerializer, OptionalSerializer, DateTimeIsoSerializer, DateIsoSerializer, \
    TimeIsoSerializer, UuidSerializer, DecimalSerializer
from serious.types import FrozenList, frozenlist, Timestamp, timestamp


class AbstractFieldSerializer(FieldSerializer):
    def __init__(self):
        super().__init__(None, None)


class TestFieldSerializer:

    def test_not_implemented(self):
        with pytest.raises(TypeError) as error:
            AbstractFieldSerializer()
        error_message = str(error)
        assert '_dump' in error_message
        assert '_load' in error_message
        assert 'fits' in error_message


def field_descriptor(type_: Type) -> FieldDescriptor:
    return FieldDescriptor('test', describe(type_), {})


def test_str_load_validation():
    serializer = StringSerializer(field_descriptor(str), None)
    ctx = SerializationContext()
    with pytest.raises(ValidationError):
        serializer.load(1, ctx)
    with pytest.raises(ValidationError):
        serializer.load(1.01, ctx)
    with pytest.raises(ValidationError):
        serializer.load(True, ctx)
    assert serializer.load('Something', ctx) == 'Something'


def test_bool_load_validation():
    serializer = BooleanSerializer(field_descriptor(bool), None)
    ctx = SerializationContext()
    with pytest.raises(ValidationError):
        serializer.load(1, ctx)
    with pytest.raises(ValidationError):
        serializer.load(1.01, ctx)
    with pytest.raises(ValidationError):
        serializer.load('Something', ctx)
    assert serializer.load(True, ctx) is True
    assert serializer.load(False, ctx) is False


def test_int_load_validation():
    serializer = IntegerSerializer(field_descriptor(int), None)
    ctx = SerializationContext()
    with pytest.raises(ValidationError):
        serializer.load(True, ctx)
    with pytest.raises(ValidationError):
        serializer.load(1.01, ctx)
    with pytest.raises(ValidationError):
        serializer.load('Something', ctx)
    assert serializer.load(1, ctx) == 1


def test_float_load_validation():
    serializer = FloatSerializer(field_descriptor(float), None)
    ctx = SerializationContext()
    with pytest.raises(ValidationError):
        serializer.load(True, ctx)
    with pytest.raises(ValidationError):
        serializer.load('Something', ctx)
    loaded_int = serializer.load(1, ctx)
    assert loaded_int == 1
    assert type(loaded_int) is float
    assert serializer.load(1.01, ctx) == 1.01


class Color(Enum):
    RED = '#ff0000'
    GREEN = '#00ff00'
    BLUE = '#0000ff'


class Constant(Enum):
    PI = 3.14
    TAU = PI * 2


class HistoricEvent(date, Enum):
    SPUTNIK = 1957, 10, 4
    LUNAR_LANDING = 1969, 7, 20


@dataclass
class EventComment:
    event: HistoricEvent
    comment: str


class TestEnumLoadValidation:

    def test_str(self):
        serializer = EnumSerializer(field_descriptor(Color), None)
        ctx = SerializationContext()
        with pytest.raises(ValidationError):
            serializer.load('#f00', ctx)
        assert serializer.load('#ff0000', ctx) is Color.RED

    def test_number(self):
        serializer = EnumSerializer(field_descriptor(Constant), None)
        ctx = SerializationContext()
        with pytest.raises(ValidationError):
            serializer.load(9.18, ctx)
        assert serializer.load(3.14, ctx) is Constant.PI

    def test_non_primitive(self):
        schema = DictSchema(EventComment)
        serializer = schema._serializer._field_serializers[0]
        assert type(serializer) is EnumSerializer
        ctx = SerializationContext()
        with pytest.raises(ValidationError):
            serializer.load('1932-11-05', ctx)
        assert serializer.load('1957-10-04', ctx) is HistoricEvent.SPUTNIK


class MockSchema:
    def field_serializer(self, desc: FieldDescriptor) -> FieldSerializer:
        return AnySerializer(desc, self)


def test_dict_load_validation():
    serializer = DictSerializer(field_descriptor(Dict[str, Any]), MockSchema())
    ctx = SerializationContext()
    with pytest.raises(ValidationError):
        serializer.load('string', ctx)
    assert serializer.load({'one': 'two'}, ctx) == {'one': 'two'}


def test_list_load_validation():
    serializer = CollectionSerializer(field_descriptor(List[Any]), MockSchema())
    ctx = SerializationContext()
    with pytest.raises(ValidationError):
        serializer.load('string', ctx)
    assert serializer.load([1, 2, 3], ctx) == [1, 2, 3]


def test_frozen_list_load_validation():
    serializer = CollectionSerializer(field_descriptor(FrozenList[Any]), MockSchema())
    ctx = SerializationContext()
    with pytest.raises(ValidationError):
        serializer.load('string', ctx)
    assert serializer.load([1, 2, 3], ctx) == frozenlist([1, 2, 3])


def test_tuple_load_validation():
    serializer = TupleSerializer(field_descriptor(Tuple[Any, Any, Any]), MockSchema())
    ctx = SerializationContext()
    with pytest.raises(ValidationError):
        serializer.load([1, 2], ctx)
    with pytest.raises(ValidationError):
        serializer.load([1, 2, 3, 4], ctx)
    with pytest.raises(ValidationError):
        serializer.load('one two three', ctx)
    assert serializer.load([1, 2, 3], ctx) == (1, 2, 3)


@dataclass
class MockDataclass:
    child: Optional['MockDataclass']


def test_dataclass_load_validation():
    schema = DictSchema(MockDataclass)
    serializer = schema._serializer._field_serializers[0]
    assert type(serializer) is OptionalSerializer
    assert type(serializer._serializer) is DataclassSerializer
    ctx = SerializationContext()
    with pytest.raises(ValidationError):
        serializer.load([1, 2], ctx)
    with pytest.raises(ValidationError):
        serializer.load('one', ctx)
    assert serializer.load(None, ctx) is None
    assert serializer.load({'child': None}, ctx) == MockDataclass(None)


def test_timestamp_load_validation():
    serializer = UtcTimestampSerializer(field_descriptor(Timestamp), None)
    ctx = SerializationContext()
    with pytest.raises(ValidationError):
        serializer.load('123421', ctx)
    assert serializer.load(123421, ctx) == timestamp(123421.0)
    assert serializer.load(123421.0, ctx) == timestamp(123421)


def test_date_time_load_validation():
    serializer = DateTimeIsoSerializer(field_descriptor(datetime), None)
    ctx = SerializationContext()
    with pytest.raises(ValidationError):
        serializer.load(123421, ctx)
    with pytest.raises(ValidationError):
        serializer.load('2018-11-17T16:55:28.456753+00:0', ctx)
    with pytest.raises(ValidationError):
        serializer.load('2018-11-7T16:55:28.456753+00:00', ctx)
    with pytest.raises(ValidationError):
        serializer.load('2018-00-7T16:55:28.456753+00:00', ctx)
    expected = datetime(2018, 11, 17, 16, 55, 28, 456753, tzinfo=timezone.utc)
    assert serializer.load('2018-11-17T16:55:28.456753+00:00', ctx) == expected


def test_date_load_validation():
    serializer = DateIsoSerializer(field_descriptor(date), None)
    ctx = SerializationContext()
    with pytest.raises(ValidationError):
        serializer.load(123, ctx)
    with pytest.raises(ValidationError):
        serializer.load('2018-14-17', ctx)
    with pytest.raises(ValidationError):
        serializer.load('2018-11-7', ctx)
    with pytest.raises(ValidationError):
        serializer.load('2018-00-7', ctx)
    assert serializer.load('2018-11-17', ctx) == date(2018, 11, 17)


def test_time_load_validation():
    serializer = TimeIsoSerializer(field_descriptor(time), None)
    ctx = SerializationContext()
    with pytest.raises(ValidationError):
        serializer.load(123, ctx)
    with pytest.raises(ValidationError):
        serializer.load('24:00:00', ctx)
    with pytest.raises(ValidationError):
        serializer.load('25:00:00', ctx)
    with pytest.raises(ValidationError):
        serializer.load('1:1:2', ctx)
    assert serializer.load('04:20:00', ctx) == time(4, 20, 00)


def test_uuid_load_validation():
    serializer = UuidSerializer(field_descriptor(UUID), None)
    ctx = SerializationContext()
    with pytest.raises(ValidationError):
        serializer.load(123421, ctx)
    with pytest.raises(ValidationError):
        serializer.load('kaalksdjfglkjsadlfjlksdjdjka', ctx)
    with pytest.raises(ValidationError):
        serializer.load('d1d61dd7-c036-47d3-a6ed-91cc2e885f-c8', ctx)
    with pytest.raises(ValidationError):
        serializer.load('d1d61dd7-c036-57d3-a6ed-91cc2e885fc8', ctx)
    uuid_s = 'd1d61dd7-c036-47d3-a6ed-91cc2e885fc8'
    assert serializer.load(uuid_s, ctx) == UUID(uuid_s)
    assert serializer.load(uuid_s.upper(), ctx) == UUID(uuid_s)


def test_decimal_load_validation():
    serializer = DecimalSerializer(field_descriptor(Decimal), None)
    ctx = SerializationContext()
    with pytest.raises(ValidationError):
        serializer.load(10, ctx)
    with pytest.raises(ValidationError):
        serializer.load(9.8, ctx)
    with pytest.raises(ValidationError):
        serializer.load('', ctx)
    assert serializer.load('9.8', ctx) == Decimal('9.8')
