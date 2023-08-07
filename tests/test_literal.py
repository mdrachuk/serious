from dataclasses import dataclass
from typing import Literal

from serious import DictModel


@dataclass
class AlmostEnum:
    value: Literal['one', 'two', 'three']


class TestSerializeLiteral:
    def setup(self):
        self.model = DictModel(AlmostEnum)

    def test_load(self):
        o = self.model.load({'value': 'one'})
        assert o.value == 'one'

    def test_dump(self):
        d = self.model.dump(AlmostEnum('two'))
        assert d == {'value': 'two'}
