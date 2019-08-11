from typing import List, Set, Tuple, Optional, FrozenSet

from serious import JsonModel, DictModel
from serious.test_utils import assert_symmetric
from tests.entities import dataclass_of
from tests.utils import with_

models = [JsonModel, DictModel]
objects = [
    dataclass_of(List[int])([1, 2, 3]),
    dataclass_of(Set[int])({1, 2, 3}),
    dataclass_of(Tuple[int, Ellipsis])(tuple([1, 2, 3])),
    dataclass_of(Tuple[int, str, int])(tuple([1, 'two', 3])),
    dataclass_of(FrozenSet[int])(frozenset([1, 2, 3])),
    dataclass_of(Optional[int])(None),
    dataclass_of(Optional[int])(3),
]


@with_(models, objects)
def test_generic_encode_and_decode_are_inverses(new_model, dc):
    assert_symmetric(new_model(type(dc)), dc)
