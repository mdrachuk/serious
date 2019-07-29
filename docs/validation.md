# Validating dataclass object
## `#__validate__(self)`
To validate instance of a dataclass on load add a `__validate__` method to it:

```python
from dataclasses import dataclass
from typing import List
from serious import DictSchema, ValidationError

@dataclass
class Order:
    lines: List[str]
    
    def __validate__(self):
        if len(self.lines) == 0:
            raise ValidationError('Order cannot be empty')

schema = DictSchema(Order)
try:
    schema.load({'lines': []})
except ValidationError as e:
    print(str(e)) # Order cannot be empty
```
## `validate(object)`

#

