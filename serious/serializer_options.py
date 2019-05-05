from __future__ import annotations

from abc import abstractmethod, ABC
from dataclasses import replace, is_dataclass
from datetime import datetime, timezone
from decimal import Decimal
from enum import Enum
from typing import _GenericAlias, List  # type: ignore # _GenericAlias exists!
from uuid import UUID

from serious.attr import Attr
from serious.field_serializers import (FieldSerializer, DirectFieldSerializer, OptionalFieldSerializer,
                                       DictFieldSerializer, CollectionFieldSerializer, DataclassFieldSerializer,
                                       MetadataFieldSerializer)
from serious.utils import _is_optional, _is_mapping, _is_collection

if False:  # To reference in typings
    from serious.serialization import SeriousSerializer

local_tz = datetime.now(timezone.utc).astimezone().tzinfo


class SerializerOption(ABC):
    @abstractmethod
    def fits(self, attr: Attr) -> bool:
        raise NotImplementedError

    @abstractmethod
    def factory(self, attr: Attr, sr: SeriousSerializer) -> FieldSerializer:
        raise NotImplementedError

    @staticmethod
    def defaults() -> List[SerializerOption]:
        return [
            MetadataSrOption(),
            OptionalSrOption(),
            MappingSrOption(),
            CollectionSrOption(),
            PrimitiveSrOption(),
            DataclassSrOption(),
            DateTimeTimestampSrOption(),
            UuidSrOption(),
            DecimalSrOption(),
            EnumSrOption(),
        ]


class MetadataSrOption(SerializerOption):
    def fits(self, attr: Attr) -> bool:
        return attr.contains_serious_metadata

    def factory(self, attr: Attr, sr: SeriousSerializer) -> FieldSerializer:
        return MetadataFieldSerializer(attr)


class OptionalSrOption(SerializerOption):
    def fits(self, attr: Attr) -> bool:
        return isinstance(attr.type, _GenericAlias) and _is_optional(attr.type)

    def factory(self, attr: Attr, sr: SeriousSerializer) -> FieldSerializer:
        present_sr = generic_item_serializer(attr, sr, type_index=0)
        return OptionalFieldSerializer(attr, present_sr)


class MappingSrOption(SerializerOption):
    def fits(self, attr: Attr) -> bool:
        return isinstance(attr.type, _GenericAlias) and _is_mapping(attr.type)

    def factory(self, attr: Attr, sr: SeriousSerializer) -> FieldSerializer:
        key_sr = generic_item_serializer(attr, sr, type_index=0)
        val_sr = generic_item_serializer(attr, sr, type_index=1)
        return DictFieldSerializer(attr, key=key_sr, value=val_sr)


class CollectionSrOption(SerializerOption):
    def fits(self, attr: Attr) -> bool:
        return isinstance(attr.type, _GenericAlias) and _is_collection(attr.type)

    def factory(self, attr: Attr, sr: SeriousSerializer) -> FieldSerializer:
        item_sr = generic_item_serializer(attr, sr, type_index=0)
        return CollectionFieldSerializer(attr, each=item_sr)


class PrimitiveSrOption(SerializerOption):
    def fits(self, attr: Attr) -> bool:
        return issubclass(attr.type, (str, int, float, bool))

    def factory(self, attr: Attr, sr: SeriousSerializer) -> FieldSerializer:
        return DirectFieldSerializer(attr, load=attr.type, dump=attr.type)


class DataclassSrOption(SerializerOption):
    def fits(self, attr: Attr) -> bool:
        return is_dataclass(attr.type)

    def factory(self, attr: Attr, sr: SeriousSerializer) -> FieldSerializer:
        dataclass_sr = sr.child_serializer(attr.type)
        return DataclassFieldSerializer(attr, dataclass_sr)


class DateTimeTimestampSrOption(SerializerOption):
    def fits(self, attr: Attr) -> bool:
        return issubclass(attr.type, datetime)

    def factory(self, attr: Attr, sr: SeriousSerializer) -> FieldSerializer:
        return DirectFieldSerializer(
            attr,
            load=lambda o: datetime.fromtimestamp(o, local_tz),  # type: ignore # gonna be float
            dump=lambda o: o.timestamp()
        )


class UuidSrOption(SerializerOption):
    def fits(self, attr: Attr) -> bool:
        return issubclass(attr.type, UUID)

    def factory(self, attr: Attr, sr: SeriousSerializer) -> FieldSerializer:
        return DirectFieldSerializer(  # type: ignore # UUID constructor in load
            attr,
            load=UUID,
            dump=lambda o: str(o)
        )


class DecimalSrOption(SerializerOption):
    def fits(self, attr: Attr) -> bool:
        return issubclass(attr.type, Decimal)

    def factory(self, attr: Attr, sr: SeriousSerializer) -> FieldSerializer:
        return DirectFieldSerializer(  # type: ignore # Decimal constructor in load
            attr,
            load=Decimal,
            dump=lambda o: str(o)
        )


class EnumSrOption(SerializerOption):
    def fits(self, attr: Attr) -> bool:
        return issubclass(attr.type, Enum)

    def factory(self, attr: Attr, sr: SeriousSerializer) -> FieldSerializer:
        return DirectFieldSerializer(attr, load=attr.type, dump=lambda o: o.value)


def generic_item_serializer(attr, sr, *, type_index):
    item_descriptor = replace(attr, type=attr.type.__args__[type_index])
    item_sr = sr.field_serializer(item_descriptor, tracked=False)
    return item_sr
