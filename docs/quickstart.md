
# Installation
Available from [PyPI][pypi]:

```shell
pip install serious
```

# Models In Short
Models are the central part of the serious API:

```python
from serious import JsonModel

model = JsonModel(Stock)

model.load('{"name": "AAPL", "price": "139.38"}')
```

You encode, decode and validate the dataclasses via model methods.

Model constructor allows to change the specifics of working with particular dataclass,
e.g. `JsonModel(Job, allow_missing=True)` will set `None` to fields marked `Optional` in `Job` dataclass 
when they are missing from loaded JSON.

There are two types of Model as of now:

1. [`JsonModel`](models.md#jsonmodel): loads/dumps JSON formatted strings
2. [`DictModel`](models.md#dictmodel): loads/dumps `dict` objects 

For more refer to [models docs](models.md).
# Simple Serialization

Having a dataclass:
```python
from dataclasses import dataclass

@dataclass
class Person:
    name: str
```

Create an instance of `JsonModel`:  
```python
from serious.json import JsonModel
    
model = JsonModel(Person)
```

And use its [dump/load methods](serialization.md#encodedecode):
```python
person = Person('Albert Einstein')

model.dump(person) # {"name": "Albert Einstein"}
```

[More on serialization.](serialization.md)

# Basic Validation

To validate instance of a dataclass upon load — add a `__validate__` method to it:
```python
from dataclasses import dataclass
from typing import List
from serious import DictModel, ValidationError

@dataclass
class Order:
    lines: List[str]
    
    def __validate__(self):
        if len(self.lines) == 0:
            raise ValidationError('Order cannot be empty')

model = DictModel(Order)
```

Now passing an invalid object for decoding to this model will result in `ValidationError`:
```python
try:
    model.load({'lines': []})
except ValidationError as e:
    print(str(e)) # Order cannot be empty
```

[More on validation.](validation.md)

[pypi]: https://pypi.org/project/serious/