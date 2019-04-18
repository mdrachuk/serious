# `serious`
[![Build Status](https://dev.azure.com/misha-drachuk/serious/_apis/build/status/mdrachuk.serious?branchName=master)](https://dev.azure.com/misha-drachuk/serious/_build/latest?definitionId=1&branchName=master)

This library provides a simple API for encoding and decoding [dataclasses](https://docs.python.org/3/library/dataclasses.html) to and from JSON.

It's recursive (see caveats below), so you can easily work with nested dataclasses.
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
- [UUID](https://docs.python.org/3/library/uuid.html#uuid.UUID) objects. They 
are encoded as `str` (JSON string).


**The [latest release](https://github.com/mdrachuk/serious/releases/latest) is compatible with Python 3.7.**

## Quickstart
`pip install dataclasses-json`

#### asjson, load

```python
from dataclasses import dataclass
from serious import asjson, load, load_all

@dataclass
class Person:
    name: str

lidatong = Person('lidatong')

# Encoding to JSON
asjson(lidatong)  # '{"name": "lidatong"}'

# Decoding from JSON
load(Person).from_('{"name": "lidatong"}')  # Person(name='lidatong')
load_all(Person).from_('[{"name": "lidatong"}, {"name": "mdrachuk"}]')  # [Person(name='lidatong'), Person(name='mdrachuk')]
```

## How do I...


### Handle missing or optional field values when decoding?

By default, any fields in your dataclass that use `default` or 
`default_factory` will have the values filled with the provided default, if the
corresponding field is missing from the JSON you're decoding.

**Decode JSON with missing field**

```python
@dataclass
class Student:
    id: int
    name: str = 'student'

serious.load(Student).from_('{"id": 1}')  # Student(id=1, name='student')
```

Notice `from_json` filled the field `name` with the specified default 'student'
when it was missing from the JSON.

Sometimes you have fields that are typed as `Optional`, but you don't 
necessarily want to assign a default. In that case, you can use the 
`infer_missing` kwarg to make `from_json` infer the missing field value as `None`.

**Decode optional field without default**

```python
@dataclass
class Tutor:
    id: int
    student: Optional[Student]
serious.load(Tutor).from_('{"id": 1}')  # Tutor(id=1, student=None)
```

Personally I recommend you leverage dataclass defaults rather than using 
`infer_missing`, but if for some reason you need to decouple the behavior of 
JSON decoding from the field's default value, this will allow you to do so.


### Override field decoder/encoder?

For example, you might want to encode/decode `datetime` objects using ISO format
rather than the default `timestamp`.

```python
from dataclasses import dataclass, field
from datetime import datetime

@dataclass
class DataClassWithIsoDatetime:
    created_at: datetime = field(
        metadata={serious: {
            'encoder': datetime.isoformat,
            'decoder': datetime.fromisoformat,
        }})
```

## A larger example

```python
from dataclasses import dataclass
from serious import asjson, load, DumpOptions
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

assert asjson(boss, DumpOptions(indent=4)) == boss_json
assert load(Boss).from_(boss_json) == boss
```


## Acknowledgements
This is a fork of [@lidatong/dataclasses-json](https://github.com/lidatong/dataclasses-json).
