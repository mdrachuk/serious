# serious
[![Build Status](https://dev.azure.com/misha-drachuk/serious/_apis/build/status/serious-release?branchName=master)](https://dev.azure.com/misha-drachuk/serious/_build/latest?definitionId=1&branchName=master)
[![Supported Python](https://img.shields.io/pypi/pyversions/serious)](https://pypi.org/project/serious/)

Python [dataclasses][dataclass] serialization and validation in a [Zen][zen] and [fast][benchmarks] manner.

**Compatible with Python 3.7+.**

On top of coupling of data with its behaviour, using proper objects adds semantic meaning to your code.
Good classes manifest the intentions behind the APIs and restrictions imposed on them.
They make code cleaner, changes become simpler to implement, and maintenance becomes cheaper.

## Basics
### Installation
`pip install serious`

### Quick Example

A regular dataclass can contain validation:
```python
from dataclasses import dataclass
from serious import ValidationError

@dataclass
class Person:
    name: str

    def __validate__(self):
        if len(self.name) == '':
            raise ValidationError('Every person needs a name')
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

### Features
- clearly define models
- make use of pure python objects
- ensure typing with mypy
- Type-annotations for all public-facing APIs.
- (optionally) ensure immutability
- define APIs
- store object JSON to document databases 
- load JSON/YAML configurations to objects


### Supported formats:
- [x] JSON
- [x] dict
- [ ] YAML
- [ ] Form data


### Supported field types
- other dataclasses
- primitives: `str`, `int`, `float`, `bool`
- dicts: only with string keys: `Dict[str, Any]`  
- lists, [sets][set], [deques][deque]: python collections of any serializable type
- [tuples][tuple] both with and without ellipsis:
    - tuples as set of independent elements (e.g. `Tuple[str, int, date]`) 
    - with ellipses, acting as a frozen list (`Tuple[str, ...]`)
- [enumerations][enum] by value:
    - of primitives (e.g. `OperatingSystem(Enum)`) 
    - typed enums (`Color(str, Enum)` and `FilePermission(IntFlag)`)
- [Decimal][decimal]: encoded to JSON as string 
- [datetime][datetime], [date][date] and [time][time]: encoded to the [ISO 8601][iso8601] formatted string
- [UUID][uuid]
- `serious.types.Timestamp`: a UTC timestamp since [UNIX epoch][epoch] as float ms value 
- custom immutable alternatives to native python types in `serious.types`: `FrozenList`, `FrozenDict`

## Encode/Decode

Both of these operations are performed by schema. Just like when using Python native `json` or `pickle`
to decode the value use `#load(value)` and to encode call `#dump(dataclass)`.

```python
from dataclasses import dataclass
from serious import JsonSchema

@dataclass
class Person:
    name: str

lidatong = Person('lidatong')
mdrachuk = Person('mdrachuk')

schema = JsonSchema(Person)

# Encoding to JSON
schema.dump(lidatong)  # '{"name": "lidatong"}'
schema.dump_many([mdrachuk, lidatong])  # '[{"name": "mdrachuk"}, {"name": "lidatong"}]'

# Decoding from JSON
schema.load('{"name": "lidatong"}')  # Person(name='lidatong')
schema.load_many('[{"name": "mdrachuk"}, {"name": "lidatong"}]')  # [Person(name='mdrachuk'), Person(name='lidatong')]
```

Multiple values can be manipulated by corresponding `#load_many(values)` and `#dump_many(dataclasses)` schema methods.

### Optionals

By default, any fields in your dataclass that use `default` or 
`default_factory` will have the values filled with the provided default, if the
corresponding field is missing from the JSON you're decoding.

**Decode JSON with missing field**

```python
from dataclasses import dataclass
from serious import JsonSchema
 
@dataclass
class Student:
    id: int
    name: str = 'student'

JsonSchema(Student, allow_missing=True).load('{"id": 1}')  # Student(id=1, name='student')
```

Notice that `name` got default value `student` when it was missing from the JSON.

If the default is missing 

**Decode optional field without default**

```python
from dataclasses import dataclass
from typing import Optional
from serious import JsonSchema


@dataclass
class Tutor:
    id: int
    student: Optional[Student]

JsonSchema(Tutor).load('{"id": 1}')  # Tutor(id=1, student=None)
```

### Override field load/dump?

For example, you might want to load/dump `datetime` objects using timestamp format rather than [ISO strings][iso8601].

```python
from dataclasses import dataclass, field
from datetime import datetime
from datetime import timezone

@dataclass
class Post:
    created_at: datetime = field(
        metadata={'serious': {
            'dump': lambda x, ctx: x.timestamp(),
            'load': lambda x, ctx: datetime.fromtimestamp(x, timezone.utc),
        }})
```

## A larger example

```python
from dataclasses import dataclass
from serious import JsonSchema
from typing import List

@dataclass(frozen=True)
class Minion:
    name: str


@dataclass(frozen=True)
class Boss:
    minions: List[Minion]

boss = Boss([Minion('evil minion'), Minion('very evil minion')])
boss_json = """
{
    "minions": [
        {
            "name": "evil minion"
        },
        {
            "name": "very evil minion"
        }
    ]
}
""".strip()

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
[zen]: https://github.com/mdrachuk/serious/ZEN.md