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
