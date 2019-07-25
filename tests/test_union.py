from dataclasses import dataclass
from typing import Union

import pytest

from serious import DictSchema
from serious.errors import ModelContainsUnion


@dataclass
class Something:
    value: Union[str, int]


def test_union():
    with pytest.raises(ModelContainsUnion):
        schema = DictSchema(Something)
