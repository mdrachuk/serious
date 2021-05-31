from dataclasses import dataclass, field
from typing import Dict, FrozenSet, List, Optional, Set, Tuple, TypeVar, Union
from uuid import UUID

from serious import FrozenList

A = TypeVar('A')


@dataclass(frozen=True)
class DataclassWithList:
    xs: List[int]


@dataclass(frozen=True)
class DataclassWithListStr:
    xs: List[str]


@dataclass(frozen=True)
class DataclassWithDict:
    kvs: Dict[str, str]


@dataclass(frozen=True)
class DataclassWithSet:
    xs: Set[int]


@dataclass(frozen=True)
class DataclassWithTuple:
    xs: Tuple[int, str]


@dataclass(frozen=True)
class DataclassWithTupleCollection:
    xs: Tuple[int, ...]


@dataclass(frozen=True)
class DataclassWithFrozenList:
    xs: FrozenList[int]


@dataclass(frozen=True)
class DataclassWithFrozenSet:
    xs: FrozenSet[int]


@dataclass(frozen=True)
class DataclassWithOptional:
    x: Optional[int]


@dataclass
class DataclassWithOptionalStr:
    x: Optional[str] = None


@dataclass(frozen=True)
class DataclassWithOptionalNested:
    x: Optional[DataclassWithOptional]


@dataclass(frozen=True)
class DataclassWithUnionIntNone:
    x: Union[int, None]


@dataclass(frozen=True)
class DataclassWithDataclass:
    dc_with_list: DataclassWithList


@dataclass(frozen=True)
class DataclassX:
    x: int


@dataclass(frozen=True)
class DataclassXs:
    xs: List[DataclassX]


@dataclass(frozen=True)
class DataclassIntImmutableDefault:
    x: int = 0


@dataclass(frozen=True)
class DataclassMutableDefaultList:
    xs: List[int] = field(default_factory=list)


@dataclass(frozen=True)
class DataclassMutableDefaultDict:
    xs: Dict[str, int] = field(default_factory=dict)


@dataclass
class DataclassWithUuid:
    id: UUID
