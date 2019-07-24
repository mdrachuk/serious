from dataclasses import dataclass
from typing import TypeVar, List

import pytest

from serious.dict import DictSchema
from serious.errors import ValidationError
from serious.validation import validate

ID = TypeVar('ID')
M = TypeVar('M')
C = TypeVar('C')


@dataclass(frozen=True)
class OrderLine:
    product: str
    count: int

    def __validate__(self):
        validate(self.count >= 0, 'Count must be a cardinal number')


@dataclass(frozen=True)
class Order:
    lines: List[OrderLine]

    def __validate__(self):
        validate(len(self.lines) > 0, 'Order cannot be empty')


class TestSimpleValidation:

    def setup_class(self):
        self.schema = DictSchema(OrderLine)
        self.valid = OrderLine('Nimbus 2000', 1)
        self.valid_d = {'product': 'Nimbus 2000', 'count': 1}
        self.invalid_d = {'product': 'Advanced Potion-Making', 'count': -1}

    def test_valid(self):
        actual = self.schema.load(self.valid_d)
        assert actual == self.valid

    def test_invalid(self):
        with pytest.raises(ValidationError):
            self.schema.load(self.invalid_d)


class TestNestedValidation:

    def setup_class(self):
        self.schema = DictSchema(OrderLine)
        self.valid = OrderLine('Nimbus 2000', 1)
        self.valid_d = {'product': 'Nimbus 2000', 'count': 1}
        self.invalid_d = {'product': 'Advanced Potion-Making', 'count': -1}

    def test_valid(self):
        actual = self.schema.load(self.valid_d)
        assert actual == self.valid

    def test_invalid(self):
        with pytest.raises(ValidationError):
            self.schema.load(self.invalid_d)
