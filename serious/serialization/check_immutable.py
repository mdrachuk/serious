"""Check that whole dataclass structure is immutable, i.e. it’s objects cannot be changed. """
__all__ = ['check_immutable']

from dataclasses import is_dataclass
from datetime import datetime, date, time
from decimal import Decimal
from enum import Enum
from typing import Iterable, Type, List, Any, Union
from uuid import UUID

from serious.descriptors import DescTypes, TypeDescriptor
from serious.errors import MutableTypesInModel
from serious.types import FrozenList, Email, Timestamp, FrozenDict

_IMMUTABLE_TYPES = {
    str, int, float, bool,
    bytes, tuple, frozenset, FrozenList, FrozenDict,
    Decimal, UUID, datetime, date, time,
    Email, Timestamp,
    Ellipsis, Enum,
}


def check_immutable(desc: TypeDescriptor, all_types: DescTypes, ensure_frozen: Union[bool, Iterable[Type]]):
    user_frozen = ensure_frozen if isinstance(ensure_frozen, Iterable) else {}
    mutable_types = extract_mutable(all_types, also_immutable=user_frozen)
    if len(mutable_types):
        raise MutableTypesInModel(desc.cls, mutable_types)


def extract_mutable(desc: DescTypes, also_immutable: Iterable[Type]) -> List[Type]:
    allowed_types = _IMMUTABLE_TYPES | set(also_immutable)
    maybe_dc = set(desc.types) - allowed_types
    restricted = [type_ for type_ in maybe_dc if not is_frozen_dc(type_)]
    return restricted


def is_frozen_dc(type_: Any) -> bool:
    return is_dataclass(type_) and type_.__dataclass_params__.frozen
