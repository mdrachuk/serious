[![Build Status](https://dev.azure.com/misha-drachuk/serious/_apis/build/status/serious-release?branchName=master)](https://dev.azure.com/misha-drachuk/serious/_build/latest?definitionId=1&branchName=master)

Python dataclasses serialization and validation.


# Installation

```pip install serious```

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

And use its [dump/load methods](#Encode/Decode):
```python
person = Person('Albert Einstein')

schema.dump(person) # {"name": "Albert Einstein"}
```

# Basic Validation
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
