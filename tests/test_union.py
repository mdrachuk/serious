from dataclasses import dataclass
from typing import Union

import pytest

from serious import DictSchema, ModelError
from serious.errors import ModelContainsUnion


@dataclass
class Something:
    value: Union[str, int]


def test_union():
    with pytest.raises(ModelContainsUnion):
        DictSchema(Something)


def test_model_contains_union_hierarchy():
    assert issubclass(ModelContainsUnion, ModelError)
