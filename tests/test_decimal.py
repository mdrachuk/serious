from dataclasses import dataclass
from decimal import Decimal

from serious import DictModel


@dataclass(frozen=True)
class Person:
    name: str
    height: Decimal


keith = Person('Keith', Decimal('1.76'))
keith_dict = dict(name='Keith', height='1.76')


class TestDecimal:
    def setup_class(self):
        self.model = DictModel(Person)

    def test_load(self):
        actual = self.model.load(keith_dict)
        assert actual == keith

    def test_dump(self):
        actual = self.model.dump(keith)
        assert actual == keith_dict
