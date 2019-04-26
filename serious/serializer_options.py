from dataclasses import dataclass, replace, is_dataclass
from datetime import datetime, timezone
from enum import Enum
from typing import Callable, _GenericAlias  # type: ignore # _GenericAlias exists!
from uuid import UUID

from serious.attr import Attr
from serious.field_serializers import (FieldSerializer, DirectFieldSerializer, OptionalFieldSerializer,
                                       DictFieldSerializer, CollectionFieldSerializer, DataclassFieldSerializer,
                                       MetadataFieldSerializer)
from serious.utils import _is_optional, _is_mapping, _is_collection

if False:  # To reference in typings
    from serious.serialization import SeriousSerializer

local_tz = datetime.now(timezone.utc).astimezone().tzinfo


@dataclass(frozen=True)
class SerializerOption:
    fits: Callable[[Attr], bool]
    factory: Callable[[Attr, 'SeriousSerializer'], FieldSerializer]

    @staticmethod
    def defaults():
        return [
            metadata,
            optional,
            mapping,
            collection,
            primitive,
            dc,
            datettime_timestamp,
            uuid,
            enum,
        ]


def _optional_sr_factory(attr: Attr, sr: 'SeriousSerializer') -> FieldSerializer:
    present_sr = sr.field_serializer(replace(attr, type=attr.type.__args__[0]), track=False)
    return OptionalFieldSerializer(attr, present_sr)


def _mapping_sr_factory(attr: Attr, sr: 'SeriousSerializer') -> FieldSerializer:
    key_sr = sr.field_serializer(replace(attr, type=attr.type.__args__[0]), track=False)
    val_sr = sr.field_serializer(replace(attr, type=attr.type.__args__[1]), track=False)
    return DictFieldSerializer(attr, key=key_sr, value=val_sr)


def _collection_sr_factory(attr: Attr, sr: 'SeriousSerializer') -> FieldSerializer:
    item_sr = sr.field_serializer(replace(attr, type=attr.type.__args__[0]), track=False)
    return CollectionFieldSerializer(attr, each=item_sr)


def _dataclass_sr_factory(attr: Attr, sr: 'SeriousSerializer') -> FieldSerializer:
    dataclass_sr = sr.child_serializer(attr.type)
    return DataclassFieldSerializer(attr, dataclass_sr)


metadata = SerializerOption(
    fits=lambda attr: attr.contains_serious_metadata,
    factory=lambda attr, sr: MetadataFieldSerializer(attr)
)

optional = SerializerOption(
    fits=lambda attr: isinstance(attr.type, _GenericAlias) and _is_optional(attr.type),
    factory=_optional_sr_factory
)

mapping = SerializerOption(
    fits=lambda attr: isinstance(attr.type, _GenericAlias) and _is_mapping(attr.type),
    factory=_mapping_sr_factory
)

collection = SerializerOption(
    fits=lambda attr: isinstance(attr.type, _GenericAlias) and _is_collection(attr.type),
    factory=_collection_sr_factory
)
primitive = SerializerOption(
    fits=lambda attr: issubclass(attr.type, (str, int, float, bool)),
    factory=lambda attr, sr: DirectFieldSerializer(attr, load=attr.type, dump=attr.type)
)

dc = SerializerOption(
    fits=lambda attr: is_dataclass(attr.type),
    factory=_dataclass_sr_factory
)
datettime_timestamp = SerializerOption(
    fits=lambda attr: issubclass(attr.type, datetime),
    factory=lambda attr, sr: DirectFieldSerializer(
        attr,
        load=lambda o: datetime.fromtimestamp(o, local_tz),  # type: ignore # gonna be float
        dump=lambda o: o.timestamp()
    )
)
uuid = SerializerOption(
    fits=lambda attr: issubclass(attr.type, UUID),
    factory=lambda attr, sr: DirectFieldSerializer(  # type: ignore # UUID constructor in load
        attr,
        load=UUID,
        dump=lambda o: str(o)
    )
)
enum = SerializerOption(
    fits=lambda attr: issubclass(attr.type, Enum),
    factory=lambda attr, sr: DirectFieldSerializer(attr, load=attr.type, dump=lambda o: o.value)
)
