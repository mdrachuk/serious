from dataclasses import dataclass, field
from typing import (Collection,
                    Deque,
                    Dict,
                    FrozenSet,
                    List,
                    Optional,
                    Set,
                    Tuple,
                    TypeVar,
                    Union)
from uuid import UUID

from marshmallow import fields

A = TypeVar('A')


@dataclass(frozen=True)
class DataClassWithList:
    xs: List[int]


@dataclass(frozen=True)
class DataClassWithListDefaultFactory:
    xs: List[int] = field(default_factory=list)


@dataclass(frozen=True)
class DataClassWithListStr:
    xs: List[str]


@dataclass(frozen=True)
class DataClassWithDict:
    kvs: Dict[str, str]


@dataclass(frozen=True)
class DataClassWithDictInt:
    kvs: Dict[int, str]


@dataclass(frozen=True)
class DataClassWithDictDefaultFactory:
    kvs: Dict[str, str] = field(default_factory=dict)


@dataclass(frozen=True)
class DataClassWithSet:
    xs: Set[int]


@dataclass(frozen=True)
class DataClassWithTuple:
    xs: Tuple[int]


@dataclass(frozen=True)
class DataClassWithFrozenSet:
    xs: FrozenSet[int]


@dataclass(frozen=True)
class DataClassWithDeque:
    xs: Deque[int]


@dataclass(frozen=True)
class DataClassWithOptional:
    x: Optional[int]


@dataclass
class DataClassWithOptionalStr:
    x: Optional[str] = None


@dataclass(frozen=True)
class DataClassWithOptionalNested:
    x: Optional[DataClassWithOptional]


@dataclass(frozen=True)
class DataClassWithUnionIntNone:
    x: Union[int, None]


@dataclass(frozen=True)
class DataClassWithDataClass:
    dc_with_list: DataClassWithList


@dataclass(frozen=True)
class DataClassX:
    x: int


@dataclass(frozen=True)
class DataClassXs:
    xs: List[DataClassX]


@dataclass(frozen=True)
class DataClassIntImmutableDefault:
    x: int = 0


@dataclass(frozen=True)
class DataClassBoolImmutableDefault:
    x: bool = False


@dataclass(frozen=True)
class DataClassMutableDefaultList:
    xs: List[int] = field(default_factory=list)


@dataclass(frozen=True)
class DataClassMutableDefaultDict:
    xs: Dict[str, int] = field(default_factory=dict)


class MyCollection(Collection[A]):
    def __init__(self, xs: Collection[A]) -> None:
        self.xs = xs

    def __contains__(self, item):
        return False

    def __iter__(self):
        return iter(self.xs)

    def __len__(self):
        return len(self.xs)

    def __eq__(self, other):
        return type(self) == type(other) and self.xs == other.xs


@dataclass(frozen=True)
class DataClassWithMyCollection:
    xs: MyCollection[int]


@dataclass
class DataClassJsonDecorator:
    x: str


@dataclass
class DataClassWithOverride:
    id: float = field(
        metadata={'m2': {
            'mm_field': fields.Integer()
        }})


@dataclass
class DataClassWithUuid:
    id: UUID


@dataclass
class DataClassDefaultListStr:
    value: List[str] = field(default_factory=list)


@dataclass
class DataClassChild:
    name: str


@dataclass
class DataClassDefaultOptionalList:
    children: Optional[List[DataClassChild]] = None


@dataclass
class DataClassList:
    children: List[DataClassChild]


@dataclass
class DataClassOptional:
    a: int
    b: Optional[int]
