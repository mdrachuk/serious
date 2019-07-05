from __future__ import annotations

from abc import abstractmethod, ABC
from collections import deque
from dataclasses import replace
from datetime import datetime, timezone
from decimal import Decimal
from enum import Enum
from typing import List, Any  # type: ignore # _GenericAlias exists!
from uuid import UUID

from serious.descriptors import FieldDescriptor
from serious.field_serializers import (FieldSerializer, DirectFieldSerializer, OptionalFieldSerializer,
                                       DictFieldSerializer, CollectionFieldSerializer, DataclassFieldSerializer,
                                       MetadataFieldSerializer, NoopSerializer)

if False:  # To reference in typings
    from serious.serializer import DataclassSerializer


# TODO:mdrachuk:2019-07-05: document every single serializer

class FieldSerializerOption(ABC):
    @abstractmethod
    def fits(self, field: FieldDescriptor) -> bool:
        raise NotImplementedError

    @abstractmethod
    def create(self, field: FieldDescriptor, sr: DataclassSerializer) -> FieldSerializer:
        raise NotImplementedError

    @staticmethod
    def defaults() -> List[FieldSerializerOption]:
        return [
            MetadataSO(),
            OptionalSO(),
            AnySO(),
            MappingSO(),
            CollectionSO(),
            PrimitiveSO(),
            DataclassSO(),
            DateTimeTimestampSO(),
            UuidSO(),
            DecimalSO(),
            EnumSO(),
        ]


class MetadataSO(FieldSerializerOption):
    def fits(self, field: FieldDescriptor) -> bool:
        return field.metadata is not None and 'serious' in field.metadata

    def create(self, field: FieldDescriptor, sr: DataclassSerializer) -> FieldSerializer:
        return MetadataFieldSerializer(field)


class OptionalSO(FieldSerializerOption):
    def fits(self, field: FieldDescriptor) -> bool:
        return field.type.is_optional

    def create(self, field: FieldDescriptor, sr: DataclassSerializer) -> FieldSerializer:
        item_descriptor = replace(field, type=field.type.non_optional())
        present_sr = sr.field_serializer(item_descriptor, tracked=False)
        return OptionalFieldSerializer(field, present_sr)


class AnySO(FieldSerializerOption):
    def fits(self, field: FieldDescriptor) -> bool:
        return field.type.cls is Any

    def create(self, field: FieldDescriptor, sr: DataclassSerializer) -> FieldSerializer:
        return NoopSerializer(field)


class MappingSO(FieldSerializerOption):
    def fits(self, field: FieldDescriptor) -> bool:
        return issubclass(field.type.cls, dict)

    def create(self, field: FieldDescriptor, sr: DataclassSerializer) -> FieldSerializer:
        key_sr = generic_item_serializer(field, sr, type_index=0)
        val_sr = generic_item_serializer(field, sr, type_index=1)
        return DictFieldSerializer(field, key=key_sr, value=val_sr)


class CollectionSO(FieldSerializerOption):
    def fits(self, field: FieldDescriptor) -> bool:
        return issubclass(field.type.cls, (list, set, frozenset, tuple, deque))

    def create(self, field: FieldDescriptor, sr: DataclassSerializer) -> FieldSerializer:
        item_sr = generic_item_serializer(field, sr, type_index=0)
        return CollectionFieldSerializer(field, each=item_sr)


class PrimitiveSO(FieldSerializerOption):
    def fits(self, field: FieldDescriptor) -> bool:
        return issubclass(field.type.cls, (str, int, float, bool))

    def create(self, field: FieldDescriptor, sr: DataclassSerializer) -> FieldSerializer:
        return DirectFieldSerializer(field, load=field.type.cls, dump=field.type.cls)


class DataclassSO(FieldSerializerOption):
    def fits(self, field: FieldDescriptor) -> bool:
        return field.type.is_dataclass

    def create(self, field: FieldDescriptor, sr: DataclassSerializer) -> FieldSerializer:
        dataclass_sr = sr.child_serializer(field)
        return DataclassFieldSerializer(field, dataclass_sr)


class DateTimeTimestampSO(FieldSerializerOption):
    def fits(self, field: FieldDescriptor) -> bool:
        return issubclass(field.type.cls, datetime)

    def create(self, field: FieldDescriptor, sr: DataclassSerializer) -> FieldSerializer:
        local_tz = datetime.now(timezone.utc).astimezone().tzinfo
        return DirectFieldSerializer(
            field,
            load=lambda o: datetime.fromtimestamp(o, local_tz),  # type: ignore # gonna be float
            dump=lambda o: o.timestamp()
        )


class DateTimeIsoSO(FieldSerializerOption):
    def fits(self, field: FieldDescriptor) -> bool:
        return issubclass(field.type.cls, datetime)

    def create(self, field: FieldDescriptor, sr: DataclassSerializer) -> FieldSerializer:
        return DirectFieldSerializer(
            field,
            load=datetime.fromisoformat,
            dump=datetime.isoformat
        )


class UuidSO(FieldSerializerOption):
    def fits(self, field: FieldDescriptor) -> bool:
        return issubclass(field.type.cls, UUID)

    def create(self, field: FieldDescriptor, sr: DataclassSerializer) -> FieldSerializer:
        return DirectFieldSerializer(  # type: ignore # UUID constructor in load
            field,
            load=UUID,
            dump=lambda o: str(o)
        )


class DecimalSO(FieldSerializerOption):
    def fits(self, field: FieldDescriptor) -> bool:
        return issubclass(field.type.cls, Decimal)

    def create(self, field: FieldDescriptor, sr: DataclassSerializer) -> FieldSerializer:
        return DirectFieldSerializer(  # type: ignore # Decimal constructor in load
            field,
            load=Decimal,
            dump=lambda o: str(o)
        )


class EnumSO(FieldSerializerOption):
    def fits(self, field: FieldDescriptor) -> bool:
        return issubclass(field.type.cls, Enum)

    def create(self, field: FieldDescriptor, sr: DataclassSerializer) -> FieldSerializer:
        return DirectFieldSerializer(field, load=field.type.cls, dump=lambda o: o.value)


def generic_item_serializer(field: FieldDescriptor, sr: DataclassSerializer, *, type_index):
    new_type = field.type.parameters[type_index]
    item_descriptor = replace(field, type=new_type)
    item_serializer = sr.field_serializer(item_descriptor, tracked=False)
    return item_serializer
