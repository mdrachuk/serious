from dataclasses import dataclass
from decimal import Decimal

from serious import DictSchema


@dataclass(frozen=True)
class Person:
    name: str
    height: Decimal


keith = Person('Keith', Decimal('1.76'))
keith_dict = dict(name='Keith', height='1.76')


class TestDecimal:
    def setup_class(self):
        self.schema = DictSchema(Person)

    def test_load(self):
        actual = self.schema.load(keith_dict)
        assert actual == keith

    def test_dump(self):
        actual = self.schema.dump(keith)
        assert actual == keith_dict
