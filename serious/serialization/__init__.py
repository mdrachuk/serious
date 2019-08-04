from __future__ import annotations

__all__ = [
    'SeriousModel',
    'FieldSerializer',
    'Loading',
    'Dumping',
    'OptionalSerializer',
    'AnySerializer',
    'EnumSerializer',
    'DictSerializer',
    'CollectionSerializer',
    'TupleSerializer',
    'StringSerializer',
    'BooleanSerializer',
    'IntegerSerializer',
    'FloatSerializer',
    'DataclassSerializer',
    'UtcTimestampSerializer',
    'DateTimeIsoSerializer',
    'DateIsoSerializer',
    'TimeIsoSerializer',
    'UuidSerializer',
    'DecimalSerializer',
]
from typing import Iterable, Type, Tuple

from .core import Loading, Dumping, SerializationStep
from .field_serializers import OptionalSerializer, AnySerializer, EnumSerializer, DictSerializer, CollectionSerializer, \
    TupleSerializer, StringSerializer, BooleanSerializer, IntegerSerializer, FloatSerializer, DataclassSerializer, \
    UtcTimestampSerializer, DateTimeIsoSerializer, DateIsoSerializer, TimeIsoSerializer, UuidSerializer, \
    DecimalSerializer
from .model import SeriousModel, FieldSerializer


def field_serializers(custom: Iterable[Type[FieldSerializer]] = tuple()) -> Tuple[Type[FieldSerializer], ...]:
    """
    Returns a frozen collection of field serializers in the default order.
    You can provide a list of custom field serializers to include them along with default serializers.
    The order in the collection defines the order in which the serializers will be tested for fitness for each field.
    """
    return tuple([
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
