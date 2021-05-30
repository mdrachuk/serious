# serious
[![PyPI](https://img.shields.io/pypi/v/serious)][pypi]
[![Build Status](https://img.shields.io/azure-devops/build/misha-drachuk/serious/2)](https://dev.azure.com/misha-drachuk/serious/_build/latest?definitionId=1&branchName=master)
[![Test Coverage](https://img.shields.io/coveralls/github/mdrachuk/serious/master)](https://coveralls.io/github/mdrachuk/serious)
[![Supported Python](https://img.shields.io/pypi/pyversions/serious)][pypi]
[![Documentation](https://img.shields.io/readthedocs/serious)][docs]

A dataclass model toolkit: serialization, validation, and more.

[Documentation][docs]


## Features
- Model definitions in pure Python.
- Validation showing up in code coverage.
- Type annotations for all public-facing APIs.
- (Optionally) ensures immutability.
- Easily extensible.
- Made for people.
- Documented rigorously.

## Basics
### Installation
Available from [PyPI][pypi]:
```shell
pip install serious
```

### Quick Example

Central part of Serious API are different [Models][doc-models].

Given a regular dataclass:
```python
from dataclasses import dataclass

@dataclass
class Person:
    name: str
```

Let’s create a `JsonModel`:  
```python
from serious.json import JsonModel
    
model = JsonModel(Person)
```

And use its [dump/load methods][doc-serialization]:
```python
person = Person('Albert Einstein')

model.dump(person) # {"name": "Albert Einstein"}
```

### Validation
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


### Supported formats:
- [x] [JSON][doc-json-model]
- [x] [Python Dictionaries][doc-dict-model]
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
from serious import JsonModel, ValidationError
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
            "type": "Fool"
        },
        {
            "name": "very evil minion",
            "type": "Worker"
        }
    ]
}"""

model = JsonModel(Boss, indent=4)

assert model.dump(boss) == boss_json
assert model.load(boss_json) == boss
```


## Acknowledgements
Initially, a fork of [@lidatong/dataclasses-json](https://github.com/lidatong/dataclasses-json).

[pypi]: https://pypi.org/project/serious/
[dataclass]: https://docs.python.org/3/library/dataclasses.html
[iso8601]: https://en.wikipedia.org/wiki/ISO_8601
[epoch]: https://en.wikipedia.org/wiki/Unix_time
[enum]: https://docs.python.org/3/library/enum.html
[decimal]: https://docs.python.org/3/library/decimal.html
[tuple]: https://docs.python.org/3/library/stdtypes.html#tuple
[list]: https://docs.python.org/3/library/stdtypes.html#list
[set]: https://docs.python.org/3/library/stdtypes.html#set
[deque]: https://docs.python.org/3.7/library/collections.html#collections.deque
[datetime]: https://docs.python.org/3.7/library/datetime.html#datetime.datetime
[date]: https://docs.python.org/3.7/library/datetime.html#datetime.date
[time]: https://docs.python.org/3.7/library/datetime.html#datetime.time
[uuid]: https://docs.python.org/3.7/library/uuid.html?highlight=uuid#uuid.UUID
[doc-types]: https://serious.readthedocs.io/en/latest/types/
[doc-models]: https://serious.readthedocs.io/en/latest/models/
[doc-json-model]: https://serious.readthedocs.io/en/latest/models/#jsonmodel
[doc-dict-model]: https://serious.readthedocs.io/en/latest/models/#dictmodel
[doc-serialization]: https://serious.readthedocs.io/en/latest/serialization/ (Serialization documentation)
[doc-validation]: https://serious.readthedocs.io/en/latest/validation/ (Validation documentation)
[docs]: https://serious.readthedocs.io/en/latest/ 
