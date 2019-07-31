
# Installation
Available from [PyPI][pypi]:

```shell
pip install serious
```

# Schemas
Schemas are the central part of the serious API:

```python
from serious import JsonSchema

schema = JsonSchema(Stock)

schema.load('{"name": "AAPL", "price": "139.38"}')
```

You encode, decode and validate the dataclasses via schema methods.

Schema constructor allows to change the specifics of working with particular dataclass,
e.g. `JsonSchema(Job, allow_missing=True)` will set `None` to fields marked `Optional` in `Job` dataclass 
when they are missing from loaded JSON.

There are two types of Schema as of now:
1. `JsonSchema`: loads/dumps JSON formatted strings
2. `DictSchema`: loads/dumps `dict` objects 

For more refer to [schemas docs](/schemas).
# Basic Serialization

Having a dataclass:
```python
from dataclasses import dataclass

@dataclass
class Person:
    name: str
```

Create an instance of `JsonSchema`:  
```python
from serious.json import JsonSchema
    
schema = JsonSchema(Person)
```

And use its [dump/load methods](/serialization#encodedecode):
```python
person = Person('Albert Einstein')

schema.dump(person) # {"name": "Albert Einstein"}
```

[More on serialization.](/serialization)

# Basic Validation

To validate instance of a dataclass upon load — add a `__validate__` method to it:
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
```

Now passing an invalid object for decoding to this schema will result in `ValidationError`:
```python
try:
    schema.load({'lines': []})
except ValidationError as e:
    print(str(e)) # Order cannot be empty
```

[More on validation.](/validation)

[pypi]: https://pypi.org/project/serious/