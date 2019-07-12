from dataclasses import dataclass
from decimal import Decimal

from serious.dict import DictSerializer


@dataclass(frozen=True)
class Person:
    name: str
    height: Decimal


schema = DictSerializer(Person)
keith = Person('Keith', Decimal('1.76'))
keith_dict = dict(name='Keith', height='1.76')


class TestDecimal:
    def test_load(self):
        actual = schema.load(keith_dict)
        assert actual == keith

    def test_dump(self):
        actual = schema.dump(keith)
        assert actual == keith_dict
