[![PyPI](https://img.shields.io/pypi/v/serious)](https://pypi.org/project/serious/)
[![Build Status](https://img.shields.io/azure-devops/build/misha-drachuk/serious/2)](https://dev.azure.com/misha-drachuk/serious/_build/latest?definitionId=1&branchName=master)
[![Supported Python](https://img.shields.io/pypi/pyversions/serious)](https://pypi.org/project/serious/)

One-- [preferable][zen] --way for object serialization and validation.


# Get It Now
Available on [PyPI][pypi]:

```shell
pip install serious
```

# Why So Serious
### Stop pushing dicts around!
On top of coupling of data with its behaviour, using proper objects adds semantic meaning to your code.
Good classes manifest the intentions of the system and restrictions imposed on it.
APIs get cleaner, changes become simpler to implement, and maintenance turns out cheaper.

### No declarative validation
All of object validation happens in its `__validate__` method by raising `ValidationError`.
This introduces multiple benefits:

- [Explicit raising][zen] of validation errors allows to see which cases are not covered by tests.
- No need to remember library-specific validator names. A set of simple `if` statements instead.
- The information is [less dense][zen] in field definitions, making them easier to read.

### Type annotations everywhere
Stay certain that no alien type will break production. Test correctness with [mypy][mypy]. 

### (Optionally) immutable dataclasses
TBD

### Easily extensible
Plug in [custom field types][custom-serializers] and [output formats][custom-model]. 
Serious is designed for versatility.

### Made for Humans
In software libraries the API is all that matters. 

If you find yourself struggling through some aspect of the library — it‘s a failure on our part. 
Please spend 30 seconds creating a [GitHub issue][issues]. No bureaucracy there! 

# Big Example

```python
from uuid import UUID
from dataclasses import dataclass
from typing import Set, Optional, List
from datetime import datetime

from serious import JsonModel, ValidationError

@dataclass(frozen=True)
class User:
    full_name: str
    username: Optional[str]
    phone: Optional[str]
    
    def __validate__(self):
        if not self.username and not self.phone:
            raise ValidationError('User must have either a phone number or a username.')

@dataclass(frozen=True)
class Message:
    author: User
    content: str
    sent_at: datetime
    
    def __validate__(self):
        if self.sent_at > datetime.now():
            raise ValidationError('A message cannot have a future timestamp.')

@dataclass(frozen=True)
class Chat:
    id: UUID
    name: str
    members: Set[User]
    transcript: List[Message]
    
    def top_member(self) -> User:
        """Member with most messages."""
        return max(self.members, key=self.message_count)
    
    def message_count(self, member: User):
        return len([m for m in self.transcript if m.author == member])




model = JsonModel(Chat)

chat = model.load('''
{
  "id": "e0b256d3-d515-4691-9057-649a93dee487",
  "name": "Great Quest",
  "members": [
    {"username": "king", "phone": null, "full_name": "King Arthur"},
    {"username": "w", "phone": null, "full_name": "Woman"},
    {"username": "dennis", "phone": null, "full_name": "Dennis"}
  ],
  "transcript": [
    {
      "author": {"username": "king", "phone": null, "full_name": "King Arthur"},
      "content": "I am your King.",
      "sent_at": "0483-07-31T11:35:09.025479"
    },
    {
      "author": {"username": "w", "phone": null, "full_name": "Woman"},
      "content": "Well, I didn’t vote for you.",
      "sent_at": "0483-07-31T11:35:09.025489"
    },
    {
      "author": {"username": "king", "phone": null, "full_name": "King Arthur"},
      "content": "You don’t vote for kings.",
      "sent_at": "0483-07-31T11:35:09.025490"
    },
    {
      "author": {"username": "w", "phone": null, "full_name": "Woman"},
      "content": "Well how’d you become king then?",
      "sent_at": "0483-07-31T11:35:09.025492"
    },
    {
      "author": {"username": "king", "phone": null, "full_name": "King Arthur"},
      "content": "The Lady of the Lake, her arm clad in the purest shimmering samite held aloft Excalibur from the bosom of the water, signifying by divine providence that I, Arthur, was to carry Excalibur. THAT is why I am your king.",
      "sent_at": "0483-07-31T11:35:09.025493"
    },
    {
      "author": {"username": "dennis", "phone": null, "full_name": "Dennis"},
      "content": "Listen, strange women lyin’ in ponds distributin’ swords is no basis for a system of government. Supreme executive power derives from a mandate from the masses, not from some farcical aquatic ceremony.",
      "sent_at": "0483-07-31T11:35:09.025495"
    }
  ]
}
''')

print(chat.top_member())  # User(full_name='King Arthur', username='king', phone=None)  
```


# Guide
1. [Quickstart][quickstart]
2. [Models][models]
3. [Serialization][serialization]
4. [Validation][validation]
5. [Supported Field Types][types]
6. [Examples][examples]
7. [Implementation][implementation]

[pypi]: https://pypi.org/project/serious/
[mypy]: http://www.mypy-lang.org
[issues]: https://github.com/mdrachuk/serious/issues
[custom-serializers]: serialization.md#custom-field-serializers
[custom-model]: models.md#custom-model
[quickstart]: quickstart.md
[models]: models.md
[serialization]: serialization.md
[validation]: validation.md
[types]: types.md
[examples]: examples.md
[implementation]: implementation.md
[zen]: zen.md (PEP20)