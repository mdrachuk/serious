from __future__ import annotations

from typing import Iterable, Type, Tuple

from .core import Loading, Dumping, SerializationStep, SeriousModel, FieldSerializer
from .field_serializers import *


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
