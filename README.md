# serious
[![PyPI](https://img.shields.io/pypi/v/serious)](https://pypi.org/project/serious/)
[![Build Status](https://img.shields.io/azure-devops/build/misha-drachuk/serious/2)](https://dev.azure.com/misha-drachuk/serious/_build/latest?definitionId=1&branchName=master)
[![Supported Python](https://img.shields.io/pypi/pyversions/serious)](https://pypi.org/project/serious/)

Python dataclasses serialization and validation.

**Compatible with Python 3.7+.**

On top of coupling of data with its behaviour, using proper objects adds semantic meaning to your code.
Good classes manifest the intentions of the system and restrictions imposed on it.
They make APIs cleaner, changes become simpler to implement, and maintenance becomes cheaper.

## Basics
### Installation
`pip install serious`

### Quick Example

Central part of Serious API are different **Schemas**.

Given a regular dataclass:
```python
from dataclasses import dataclass

@dataclass
class Person:
    name: str
```

Let’s create a `JsonSchema`:  
```python
from serious.json import JsonSchema
    
schema = JsonSchema(Person)
```

And use its [dump/load methods][doc-serialization]:
```python
person = Person('Albert Einstein')

schema.dump(person) # {"name": "Albert Einstein"}
```

#### Validation
To add validation to the example above all we need is to add `__validate__` method to person:
```python
from dataclasses import dataclass
from typing import Optional
from serious import ValidationError, Email

@dataclass
class Person:
    name: str
    email: Optional[Email]
    phone: Optional[str]

    def __validate__(self):
        if len(self.name) == 0:
            raise ValidationError('Every person needs a name')
        if self.phone is None and self.email is None:
            raise ValidationError('At least some contact should be present')
```

[More on validation.][doc-validation]

### Features
- Model definitions in pure Python.
- Validation showing up in code coverage.  
- Type annotations for all public-facing APIs.
- (Optionally) ensures immutability.
- Easily extensible.
- Documented for Humans.


### Supported formats:
- [x] [JSON][doc-json-schema]
- [x] [Python Dictionaries][doc-dict-schema]
- [ ] YAML
- [ ] Form data


### Supported field types
[More in docs.][doc-types]

- Other dataclasses
- Primitives: `str`, `int`, `float`, `bool`
- Dictionaries: only with string keys: `Dict[str, Any]`  
- Lists, [sets][set], [deques][deque]: python collections of any serializable type
- [Tuples][tuple] both with and without ellipsis:
    - tuples as set of independent elements (e.g. `Tuple[str, int, date]`) 
    - with ellipses, acting as a frozen list (`Tuple[str, ...]`)
- [Enumerations][enum] by value:
    - of primitives (e.g. `OperatingSystem(Enum)`) 
    - typed enums (`Color(str, Enum)` and `FilePermission(IntFlag)`)
- [Decimal][decimal]: encoded to JSON as string 
- [Datetime][datetime], [date][date] and [time][time]: encoded to the [ISO 8601][iso8601] formatted string
- [UUID][uuid]
- `serious.types.Timestamp`: a UTC timestamp since [UNIX epoch][epoch] as float ms value 
- `serious.types.Email`: a string Tiny Type that supports validation and contains additional properties 
- custom immutable alternatives to native python types in `serious.types`: `FrozenList`, `FrozenDict`

## A bigger example

```python
from dataclasses import dataclass
from serious import JsonSchema, ValidationError
from typing import List
from enum import Enum

class Specialty(Enum):
    Worker = 1
    Fool = 2


@dataclass(frozen=True)
class Minion:
    name: str
    type: Specialty


@dataclass(frozen=True)
class Boss:
    name: str
    minions: List[Minion]
    
    def __validate__(self):
        if len(self.minions) < 2:
            raise ValidationError('What kind of boss are you?')


boss = Boss("me", [Minion('evil minion', Specialty.Fool), Minion('very evil minion', Specialty.Worker)])
boss_json = """{
    "name": "me",
    "minions": [
        {
            "name": "evil minion",
            "type": 2
        },
        {
            "name": "very evil minion",
            "type": 1
        }
    ]
}"""

schema = JsonSchema(Boss, indent=4)

assert schema.dump(boss) == boss_json
assert schema.load(boss_json) == boss
```


## Acknowledgements
Initially, a fork of [@lidatong/dataclasses-json](https://github.com/lidatong/dataclasses-json).

[dataclass]: https://docs.python.org/3/library/dataclasses.html
[iso8601]: https://en.wikipedia.org/wiki/ISO_8601
[epoch]: https://en.wikipedia.org/wiki/Unix_time
[enum]: https://docs.python.org/3/library/enum.html
[decimal]: https://docs.python.org/3/library/decimal.html
[tuple]: https://docs.python.org/3/library/stdtypes.html#tuple
[list]: https://docs.python.org/3/library/stdtypes.html#list
[set]: https://docs.python.org/3/library/stdtypes.html#set
[deque]: https://docs.python.org/3.7/library/collections.html#collections.deque
[datetime]: https://docs.python.org/3.7/library/datetime.html?highlight=datetime#datetime.datetime
[date]: https://docs.python.org/3.7/library/datetime.html?highlight=datetime#datetime.date
[time]: https://docs.python.org/3.7/library/datetime.html?highlight=datetime#datetime.time
[uuid]: https://docs.python.org/3.7/library/uuid.html?highlight=uuid#uuid.UUID
[doc-types]: TBD
[doc-json-schema]: TBD
[doc-dict-schema]: TBD
[doc-serialization]: TBD
[doc-validation]: TBD
