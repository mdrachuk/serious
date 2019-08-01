### Primitives (`str`, `int`, `float`, `bool`)

Fields annotated as primitive types stay themselves during serialization.

Fields marked as primitive type subclasses are dumped to their corresponding primitive type 
and loaded by supplying the primitive value as a first argument to the fields type.
So an instance of `class Rating(int)` will be transformed to an `int` during _dump_
and its integer value will be provided to Rating constructor during _load_: `Rating(value)`.

### Dataclasses
Any dataclass can be used and it will be serialized to a dict/JSON object. 

### Dictionaries
Dictionary fields are supported as long as they have string keys: `Dict[str, Any]`. 

Most probably you should not use this dictionary as field type. 
If the model for the field is defined use a dataclass instead.

####`FrozenDict`
`serious.types.FrozenDict` acts like a dictionary that cannot be changed. 
You cannot set new items, or change, or remove existing items after a frozen dictionary
is created. 

### Lists, Sets, Deques
These collection types are serialized to/from a list.

Subclassing them will also result in an object that will be serialized to list.
During deserialization the list will be passed to a type constructor as a single parameter.

####`FrozenList`
`serious.types.FrozenList` is a list that cannot be changed. You cannot add new items, change,
or remove existing ones.

### Tuples
In python tuple is an immutable ordered collection of objects, but it’s type can be defined in two ways:
- with ellipses (`Tuple[str, ...]`) which makes it effectively a frozen list;
- without ellipses (e.g. `Tuple[str, int, date]`) which defines a heterogeneous set of elements.

### Enums
Serious works with enums by value. Usually enums do not define element types (e.g. `OperatingSystem(Enum)`).
When this happens serious does not process values in any way, which will work fine if the values of primitive types,
like `str` or `int`, but can fail in other cases.

Another approach to enums allows specifying the enum type as its’s parent class:
- `Color(str, Enum)` will serialize each enum value as `str`;
- `HistoricEvent(date, Enum)` will treat each value as Python `date` object, etc.

Also special enums like `Flag` or `IntFlag` can basically be defined as `IntFlag(int, Enum)`, so they work out of box. 

### Generics
Dataclasses with generic parameters work just fine.
Both passing the parameters directly and inheriting other generic classes works.
For example, with a generic Envelope class:  
```python
from dataclasses import dataclass
from typing import TypeVar, Generic
from uuid import UUID

M = TypeVar('M')

@dataclass(frozen=True)
class Envelope(Generic[M]):
    id: UUID
    message: M
``` 

A model can be created directly with Envelope of str:
```python
from serious import DictModel

model = DictModel(Envelope[str])
``` 

Or alternatively, with a subclass:
```python
@dataclass
class OrderEnvelope(Envelope[Order]):
    # id: UUID and message: Order are inherited from superclass
    description: str
    

order_model = DictModel(OrderEnvelope)
```

### Decimal
[From Python docs][decimal]:
> Decimal numbers can be represented exactly. 
> In contrast, numbers like 1.1 and 2.2 do not have exact representations in binary floating point. 
> End users typically would not expect 1.1 + 2.2 to display as 3.3000000000000003 as it does with binary floating point.

To support this precision decimal values are serialized to a string: `Decimal('10.5')` to `"10.5"`.

### UUID
[UUID][uuid] is short for universally unique identifier. It is a 128-bit number that is getting serialized to a hex 
representation.

Here’s an example of UUID serialized to hex string: `16fd2706-8baf-433b-82eb-8c7fada847da`.

### datetime, date and time
Python `datetime` module [datetime][datetime], [date][date] and [time][time] objects
are encoded to the [ISO 8601][iso8601] formatted string.

|  Type  |        Format       |Example                  |
|--------|---------------------|-------------------------|
|datetime|`<date>T<time>+00:00`|2019-07-29T17:45:05+10:00|
|date    |`YYYY-MM-DD`         |2019-07-29               |
|time    |`hh:mm:ss.sss`       |07:00:00                 |

----

## Serious types
### Timestamp
`serious.types.Timestamp` is a an immutable(frozen) UTC timestamp.

It is serialized to a float value with whole number part being a number of ms since [UNIX epoch][epoch]

It can be constructed from a single:
- datetime object;
- ISO 8601 formatted string;
- number of seconds since UNIX epoch in int or float;
- or another Timestamp object.

### Email
`serious.types.Email` is a string that conforms to email format, so it can have additional properties: 
username, label, domain. 

Having a separate class instead of using regular string not only allows for additional methods and computed properties, 
but also lets static type checkers more data to validate, and makes code more readable adding semantics to data. 
It is a great example of implementing a [Tiny Types pattern][tiny-types].

```python
assert Email('leonardo@vinci.it') == Email('LEONARDO@vInCi.It') 
assert Email('leonardo@vinci.it').username == 'leonardo' 
assert Email('leonardo@vinci.it').label is None 
assert Email('leonardo+paintings@vinci.it').label == 'paintings' 
```

[uuid]: https://docs.python.org/3/library/uuid.html
[decimal]: https://docs.python.org/3.7/library/decimal.html
[iso8601]: https://en.wikipedia.org/wiki/ISO_8601
[datetime]: https://docs.python.org/3.7/library/datetime.html?highlight=datetime#datetime.datetime
[date]: https://docs.python.org/3.7/library/datetime.html?highlight=datetime#datetime.date
[time]: https://docs.python.org/3.7/library/datetime.html?highlight=datetime#datetime.time
[epoch]: https://en.wikipedia.org/wiki/Unix_time
[tiny-types]: TODO 