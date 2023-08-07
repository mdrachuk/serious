from collections import namedtuple
from dataclasses import dataclass
from decimal import Decimal
from typing import List, Set, Tuple, Optional, FrozenSet, Type

from serious import JsonModel, DictModel
from serious.test_utils import assert_symmetric
from tests.utils import with_

Ex = namedtuple('Ex', ['value_type', 'value'])

models = [JsonModel, DictModel]
objects = [
    Ex(int, 3),
    Ex(float, 0.7),
    Ex(str, '¡hellø!'),
    Ex(Decimal, Decimal('3')),
    Ex(List[int], [1, 2, 3]),
    Ex(Set[int], {1, 2, 3}),
    Ex(Tuple[int, Ellipsis], tuple([1, 2, 3])),
    Ex(Tuple[int, str, int], tuple([1, 'two', 3])),
    Ex(FrozenSet[int], frozenset([1, 2, 3])),
    Ex(Optional[int], None),
    Ex(Optional[int], 3),
]


@with_(models, objects)
def test_generic_encode_and_decode_are_inverses(new_model, example: Ex):
    type_ = generic_dataclass(example.value_type)
    model = new_model(type_)
    instance = type_(example.value)
    assert_symmetric(model, instance)


def generic_dataclass(type_: Type):
    @dataclass(frozen=True)
    class GenDataclass:
        value: type_

    return GenDataclass
