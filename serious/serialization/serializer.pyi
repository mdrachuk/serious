from __future__ import annotations

from abc import ABC
from typing import TypeVar, Generic

from serious.descriptors import Descriptor
from . import SeriousModel
from .context import SerializationContext

OBJECT_TYPE = TypeVar("OBJECT_TYPE")  # Python model value
PRIMITIVE_TYPE = TypeVar("PRIMITIVE_TYPE")  # Serialized value


class Serializer(Generic[OBJECT_TYPE, PRIMITIVE_TYPE], ABC):
    type: Descriptor
    root: SeriousModel

    def __init__(self, type: Descriptor, root: SeriousModel): ...

    @classmethod
    def fits(cls, desc: Descriptor) -> bool: ...

    def load(self, primitive: PRIMITIVE_TYPE, ctx: SerializationContext) -> OBJECT_TYPE: ...

    def dump(self, o: OBJECT_TYPE, ctx: SerializationContext) -> PRIMITIVE_TYPE: ...

    def load_nested(self, step: str, primitive: PRIMITIVE_TYPE, ctx: SerializationContext) -> OBJECT_TYPE: ...

    def dump_nested(self, step: str, o: OBJECT_TYPE, ctx: SerializationContext) -> PRIMITIVE_TYPE: ...
