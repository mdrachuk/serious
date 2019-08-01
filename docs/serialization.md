# Basic Serialization

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

And use its [dump/load methods](#Encode/Decode):
```python
person = Person('Albert Einstein')

model.dump(person) # {"name": "Albert Einstein"}
```


## Encode/Decode

Both of these operations are performed by a model. Just like when using Python native `json` or `pickle`
to decode the value use `#load(value)` and to encode call `#dump(dataclass)`.

```python
from dataclasses import dataclass
from serious import JsonModel

@dataclass
class Person:
    name: str

lidatong = Person('lidatong')
mdrachuk = Person('mdrachuk')

model = JsonModel(Person)

# Encoding to JSON
model.dump(lidatong)  # '{"name": "lidatong"}'
model.dump_many([mdrachuk, lidatong])  # '[{"name": "mdrachuk"}, {"name": "lidatong"}]'

# Decoding from JSON
model.load('{"name": "lidatong"}')  # Person(name='lidatong')
model.load_many('[{"name": "mdrachuk"}, {"name": "lidatong"}]')  # [Person(name='mdrachuk'), Person(name='lidatong')]
```

Multiple values can be manipulated by corresponding `#load_many(values)` and `#dump_many(dataclasses)` model methods.

### Optionals

By default, any fields in your dataclass that use `default` or 
`default_factory` will have the values filled with the provided default, if the
corresponding field is missing from the JSON you're decoding.

**Decode JSON with missing field**

```python
from dataclasses import dataclass
from serious import JsonModel
 
@dataclass
class Student:
    id: int
    name: str = 'student'

JsonModel(Student, allow_missing=True).load('{"id": 1}')  # Student(id=1, name='student')
```

Notice that `name` got default value `student` when it was missing from the JSON.

If the default is missing 

**Decode optional field without default**

```python
from dataclasses import dataclass
from typing import Optional
from serious import JsonModel


@dataclass
class Tutor:
    id: int
    student: Optional[Student]

JsonModel(Tutor).load('{"id": 1}')  # Tutor(id=1, student=None)
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


# Custom Field Serializers