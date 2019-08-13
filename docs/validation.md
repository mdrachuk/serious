# Validating Objects

By default, any “loaded” object is validated before being returned.
This can be overridden by passing `validate_on_load` and `validate_on_dump` options to models. 

To add validators to an object just create a `__validate__(self)` method in it.
 
## `def __validate__(self) -> None:`

This method single-handedly ensures all of objects [invariants](https://en.wikipedia.org/wiki/Class_invariant) 
instead of smearing validation all over the place.

In case of invalid state the method should raise a `ValidationError`. 
This approach allows to check that both positive and negative scenarios are covered by tests.
 
This method can be defined in any custom object. Serious does not discriminate and checks every created object.

`__validate__` should not return anything. Only way to fail validation is to raise a `ValidationError`.

_Example:_

```python
from dataclasses import dataclass
from decimal import Decimal
from typing import List

from serious import ValidationError, JsonModel


@dataclass
class OrderLine:
    price: Decimal


@dataclass
class Order:
    total: Decimal
    lines: List[OrderLine]

    def __validate__(self):
        if self.total != sum(line.price for line in self.lines):
            raise ValidationError('Order total does not match the sum of order lines')


try:
    JsonModel(Order).load('{"total": "9.99", "lines": [{"price": "7.0"}, {"price": "3.0"}]}')
except ValidationError as e:
    print(str(e))  # Order total does not match the sum of order lines

```
## `def validate(object: T) -> T:`

`serious.validate` function executes object `__validate__` method if it’s present.

_For example using the Order model defined above:_ 

```python
from serious import validate

try:
    validate(Order(Decimal('9.99'), lines=[
        OrderLine(Decimal('6.99')),
        OrderLine(Decimal('2.99'))
    ]))
except ValidationError as e:
    print(str(e)) # Order total does not match the sum of order lines
```

_Or for a valid case:_

```python
validated_order = validate(Order(Decimal('7'), lines=[
    OrderLine(Decimal('3.50')),
    OrderLine(Decimal('3.50'))
]))
print(validated_order)
# Order(total=Decimal('7'), lines=[OrderLine(price=Decimal('3.50')), OrderLine(price=Decimal('3.50'))])
```