from abc import ABC
from dataclasses import dataclass
from typing import TypeVar, List

import pytest

from serious import ValidationError, DictModel, JsonModel

ID = TypeVar('ID')
M = TypeVar('M')
C = TypeVar('C')


@dataclass(frozen=True)
class OrderLine:
    product: str
    count: int

    def __validate__(self):
        if self.count < 0:
            raise ValidationError('Count must be a cardinal number')


@dataclass(frozen=True)
class Order:
    lines: List[OrderLine]

class AbstractValidation:

    def test_valid(self):
        actual = self.model.load(self.valid_d)
        assert actual == self.valid

    def test_invalid(self):
        with pytest.raises(ValidationError):
            self.model.load(self.invalid_d)

class TestSimpleValidation(AbstractValidation):

    def setup_class(self):
        self.model = DictModel(OrderLine)
        self.valid = OrderLine('Nimbus 2000', 1)
        self.valid_d = {'product': 'Nimbus 2000', 'count': 1}
        self.invalid_d = {'product': 'Advanced Potion-Making', 'count': -1}


class TestNestedValidation(AbstractValidation):

    def setup_class(self):
        self.model = DictModel(Order)
        self.valid = Order([OrderLine('Nimbus 2000', 1)])
        self.valid_d = {'lines': [{'product': 'Nimbus 2000', 'count': 1}]}
        self.invalid_d = {'lines': [{'product': 'Advanced Potion-Making', 'count': -1}]}


@dataclass
class Treasure:
    name: str
    blessing: str
    curse: str

    def __validate__(self):
        if not self.blessing and not self.curse:
            raise ValidationError('What kind of treasure does not have neither a curse or a blessing')


class AbstractValidationOptions(ABC):
    new_model = NotImplementedError
    valid_data = NotImplementedError
    invalid_data = NotImplementedError
    valid_o = Treasure('The Lost Ark of the Covenant', '', 'Faces melt off skulls, heads explode.')
    invalid_o = Treasure('The Amber Room', '', '')

    def test_on_default_is_on_load_only(self):
        model = self.new_model(Treasure)
        assert model.load(self.valid_data)
        with pytest.raises(ValidationError):
            model.load(self.invalid_data)
        assert model.dump(self.valid_o)
        assert model.dump(self.invalid_o)

    def test_on_load_only(self):
        model = self.new_model(Treasure, validate_on_load=True, validate_on_dump=False)
        assert model.load(self.valid_data)
        with pytest.raises(ValidationError):
            model.load(self.invalid_data)
        assert model.dump(self.valid_o)
        assert model.dump(self.invalid_o)

    def test_on_dump_only(self):
        model = self.new_model(Treasure, validate_on_load=False, validate_on_dump=True)
        assert model.load(self.valid_data)
        assert model.load(self.invalid_data)
        assert model.dump(self.valid_o)
        with pytest.raises(ValidationError):
            model.dump(self.invalid_o)


class TestJsonValidationOptions(AbstractValidationOptions):
    new_model = JsonModel
    valid_data = '{"name": "Holy Grail", "blessing": "happiness, eternal youth, infinite abundance", "curse": ""}'
    invalid_data = '{"name": "Faberg\\u00e9 egg", "blessing": "", "curse": ""}'


class TestDictValidationOptions(AbstractValidationOptions):
    new_model = DictModel
    valid_data = {'name': 'Holy Grail', 'blessing': 'happiness, eternal youth, infinite abundance', 'curse': ''}
    invalid_data = {'name': 'Fabergé egg', 'blessing': '', 'curse': ''}