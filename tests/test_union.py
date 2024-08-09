from dataclasses import dataclass
from typing import Union

import pytest

from serious import JsonModel


@dataclass(frozen=True)
class DataWithUnion:
    something: Union[str, int]


@dataclass(frozen=True)
class DataWithSymbolUnion:
    something: str | int


@pytest.mark.parametrize('type_', [DataWithUnion, DataWithSymbolUnion])
def test_load(type_):
    model = JsonModel(type_)

    union = type_('test')
    union_json = '{"something": {"__type__": "str", "__value__": "test"}}'
    assert model.load(union_json) == union

    int_union = type_(69)
    int_union_json = '{"something": {"__type__": "int", "__value__": 69}}'
    assert model.load(int_union_json) == int_union


@pytest.mark.parametrize('type_', [DataWithUnion, DataWithSymbolUnion])
def test_dump(type_):
    model = JsonModel(type_)

    union = type_('test')
    union_json = '{"something": {"__type__": "str", "__value__": "test"}}'
    assert model.dump(union) == union_json

    int_union = type_(-1)
    int_union_json = '{"something": {"__type__": "int", "__value__": -1}}'
    assert model.dump(int_union) == int_union_json
