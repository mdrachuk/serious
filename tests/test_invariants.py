from collections import deque

from hypothesis import given
from hypothesis.strategies import frozensets, integers, lists, one_of, sets, tuples

from serious.json import schema
from tests.entities import (DataClassWithDeque, DataClassWithFrozenSet,
                            DataClassWithList, DataClassWithOptional,
                            DataClassWithSet, DataClassWithTuple)
from tests.hypothesis2 import examples
from tests.hypothesis2.strategies import deques, optionals

dcconss_strategies_conss = [(DataClassWithList, lists, list, [1]),
                            (DataClassWithSet, sets, set, [1]),
                            (DataClassWithTuple, tuples, tuple, [1]),
                            (DataClassWithFrozenSet, frozensets, frozenset, [1]),
                            (DataClassWithDeque, deques, deque, [1]),
                            (DataClassWithOptional, optionals, lambda x: x, 1)]


@given(one_of(*[strategy_fn(integers()).map(dccons) for dccons, strategy_fn, *_ in dcconss_strategies_conss]))
@examples(*[dccons(cons(input)) for dccons, _, cons, input in dcconss_strategies_conss])
def test_generic_encode_and_decode_are_inverses(dc):
    s = schema(type(dc))
    assert s.load(s.dump(dc)) == dc
