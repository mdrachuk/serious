from hypothesis import given
from hypothesis.strategies import frozensets, integers, lists, one_of, sets, tuples

from serious import JsonModel
from serious.test_utils import assert_symmetric
from tests.entities import (DataclassWithFrozenSet, DataclassWithList, DataclassWithOptional,
                            DataclassWithSet, DataclassWithTuple)
from tests.hypothesis2 import examples
from tests.hypothesis2.strategies import optionals

dcconss_strategies_conss = [
    (DataclassWithList, lists, list, [1]),
    (DataclassWithSet, sets, set, [1]),
    (DataclassWithTuple, tuples, tuple, [1]),
    (DataclassWithFrozenSet, frozensets, frozenset, [1]),
    (DataclassWithOptional, optionals, lambda x: x, 1)
]


@given(one_of(*[strategy_fn(integers()).map(dccons) for dccons, strategy_fn, *_ in dcconss_strategies_conss]))
@examples(*[dccons(cons(input)) for dccons, _, cons, input in dcconss_strategies_conss])
def test_generic_encode_and_decode_are_inverses(dc):
    assert_symmetric(JsonModel(type(dc)), dc)
