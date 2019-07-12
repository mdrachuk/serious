# serious
[![Build Status](https://dev.azure.com/misha-drachuk/serious/_apis/build/status/serious-release?branchName=master)](https://dev.azure.com/misha-drachuk/serious/_build/latest?definitionId=1&branchName=master)

This library is for JSON encoding/decoding and validation of [dataclasses](https://docs.python.org/3/library/dataclasses.html) without magic.

In addition to the supported types in the 
[py to JSON table](https://docs.python.org/3/library/json.html#py-to-json-table), this library supports the following:
- any arbitrary [Collection](https://docs.python.org/3/library/collections.abc.html#collections.abc.Collection) type is supported.
[Mapping](https://docs.python.org/3/library/collections.abc.html#collections.abc.Mapping) types are encoded as JSON objects and `str` types as JSON strings. 
Any other Collection types are encoded into JSON arrays, but decoded into the original collection types.
- [datetime](https://docs.python.org/3/library/datetime.html#available-types) 
objects. `datetime` objects are encoded to `float` (JSON number) using 
[timestamp](https://docs.python.org/3/library/datetime.html#datetime.datetime.timestamp).
As specified in the `datetime` docs, if your `datetime` object is naive, it will 
assume your system local timezone when calling `.timestamp()`. JSON nunbers 
corresponding to a `datetime` field in your dataclass are decoded 
into a datetime-aware object, with `tzinfo` set to your system local timezone.
Thus, if you encode a datetime-naive object, you will decode into a 
datetime-aware object. This is important, because encoding and decoding won't 
strictly be inverses. See this section if you want to override this default
behavior (for example, if you want to use ISO).
- [Decimal](https://docs.python.org/3/library/decimal.html) objects as strings.
- [UUID](https://docs.python.org/3/library/uuid.html#uuid.UUID) objects as strings.
- [Enums](https://docs.python.org/3/library/enum.html) objects by values.


**Compatible with Python 3.7.**

## Quickstart
`pip install serious`

#### schema.load() and schema.dump()

```python
from dataclasses import dataclass
from serious.json import JsonSerializer

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

## How do I...


### Handle missing or optional field values when decoding?

By default, any fields in your dataclass that use `default` or 
`default_factory` will have the values filled with the provided default, if the
corresponding field is missing from the JSON you're decoding.

**Decode JSON with missing field**

```python
from dataclasses import dataclass
from serious.json import JsonSchema
 
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
@dataclass
class Tutor:
    id: int
    student: Optional[Student]

serious.json.JsonSchema(Tutor).load('{"id": 1}')  # Tutor(id=1, student=None)
```

Personally I recommend you leverage dataclass defaults rather than using 
`infer_missing`, but if for some reason you need to decouple the behavior of 
JSON decoding from the field's default value, this will allow you to do so.


### Override field load/dump?

For example, you might want to encode/decode `datetime` objects using ISO format
rather than the default `timestamp`.

```python
from dataclasses import dataclass, field
from datetime import datetime

@dataclass
class DataclassWithIsoDatetime:
    created_at: datetime = field(
        metadata={'serious': {
            'dump': datetime.isoformat,
            'load': datetime.fromisoformat,
        }})
```

## A larger example

```python
from dataclasses import dataclass
from serious.json import JsonSchema
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
This is a fork of [@lidatong/dataclasses-json](https://github.com/lidatong/dataclasses-json).
