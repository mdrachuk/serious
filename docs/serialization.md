## Encode/Decode

Both of these operations are performed by a [model](models.md). 
Just like when using Python native [json][py-json] or [pickle][py-pickle] in Serious we `#load(value)`
and `#dump(dataclass)`. The argument and return types of this methods are defined by the model in use
 ([JsonModel][json-model], [DictModel][dict-model]).

So having a dataclass:
```python
from dataclasses import dataclass

@dataclass
class Character:
    name: str
```

Create an instance of `JsonModel`:  
```python
from serious import JsonModel
    
model = JsonModel(Character)
```

And use its load/dump methods:
```python
lancelot = Character('Sir Lancelot')
assert model.load('{"name": "Sir Lancelot"}') == lancelot

robin = Character('Sir Robin')
galahad = Character('Galahad')
assert model.dump_many([robin, galahad]) == '[{"name": "Sir Robin"}, {"name": "Galahad"}]'

bridgekeeper = Character('Bridgekeeper')
assert model.dump(bridgekeeper) == '{"name": "Bridgekeeper"}'

king = Character('King Arthur')
bedevere = Character('Sir Bedevere')
assert model.load_many('[{"name": "King Arthur"}, {"name": "Sir Bedevere"}]') == [king, bedevere]
```

Multiple values can be manipulated by corresponding `#load_many(values)` and `#dump_many(dataclasses)` model methods.


### Field Serializers
Internally serialization is performed by field serializers (subclasses of `serious.serialization.FieldSerializer`).
A list of them is provided to the model, each checked for fitness against the dataclass field.
The first serializer class that fits the field is instantiated and used to load/dump fields values.

#### Field Serializer API

<dl>
    <dt><pre>def __init__(self, field: FieldDescriptor, root_model: SeriousModel):</pre></dt>
    <dd>
    <p>A constructor from a field descriptor and root model.
    <p>The descriptor contains information about field type, generic parameters and field metadata. 
    <p>Root model can be accessed for model configuration. 
    </dd>
    <dt><pre>@classmethod
@abstractmethod
def fits(cls, field: FieldDescriptor) -> bool:</pre></dt>
    <dd>A predicate returning <code>True</code> if this serializer fits to load/dump data for the provided field.</dd>
    <dt><pre>@abstractmethod
def load(self, value: Primitive, ctx: Context) -> Any:</pre></dt>
    <dd>Loads a primitive value to a value supported by the serializer (e.g. dict -> dataclass).</dd>
    <dt><pre>@abstractmethod
def dump(self, value: Any, ctx: Context) -> Primitive:</pre></dt>
    <dd>Dumps the field value to a primitive value (e.g. datetime -> str).</dd>
</dl>

## Custom Field Serializers
To create a custom field serializer you need to subclass the `FieldSerializer` and 
implement its `fits`, `load` and `dump` methods. 

For a new serializer to be used in model it should be included in the [`serializers`][model-init-serializers]
constructor parameter.
You can make use of `serious.serialization.field_serializers` instead of constructing this list yourself. 

`field_serializers` function returns a frozen collection of field serializers in the default order 
when called without parameters. 
You can provide a list of custom field serializers to include them after metadata and optional serializers:

```python
def field_serializers(custom: Iterable[Type[FieldSerializer]] = tuple()) -> Tuple[Type[FieldSerializer], ...]:
    return tuple([
        OptionalSerializer,
        AnySerializer,
        EnumSerializer,
        *custom,
        DictSerializer,
        CollectionSerializer,
        TupleSerializer,
        StringSerializer,
        BooleanSerializer,
        IntegerSerializer,
        FloatSerializer,
        DataclassSerializer,
        UtcTimestampSerializer,
        DateTimeIsoSerializer,
        DateIsoSerializer,
        TimeIsoSerializer,
        UuidSerializer,
        DecimalSerializer,
    ])
```

### Example

```python
from dataclasses import dataclass
from decimal import Decimal
from typing import Union, List

from serious import DictModel, ValidationError, TypeDescriptor
from serious.serialization import FieldSerializer, field_serializers

Number = Union[int, float, Decimal]


class Point:
    x: Decimal
    y: Decimal

    def __init__(self, x: Number, y: Number):
        self.x = round(Decimal(x), 2)
        self.y = round(Decimal(y), 2)

    def __repr__(self):
        return f'<Point x:{self.x} y:{self.y}>'


class PointSerializer(FieldSerializer):

    @classmethod
    def fits(cls, desc: TypeDescriptor) -> bool:
        return issubclass(desc.cls, Point)

    def load(self, value, ctx):
        self._validate_raw(value)
        return Point(Decimal(value[0]), Decimal(value[1]))

    def dump(self, value, ctx):
        return [str(value.x), str(value.y)]
    
    @staticmethod
    def _validate_raw(value):
        if not isinstance(value, list) or len(value) != 2:
            raise ValidationError('Point should be an array with x and y coordinates')


@dataclass
class Area:
    """An area inside the bounds defined by a set of points."""
    points: List[Point]


model = DictModel(Area, serializers=field_serializers([PointSerializer]))
```
This gets us:
```python
>>> print('Loaded:', model.load({'points': [['1', '1'], ['2', '3'], ['4', '3.2']]}))
Loaded: Area(points=[<Point x:1.00 y:1.00>, <Point x:2.00 y:3.00>, <Point x:4.00 y:3.20>])

>>> print('Dumped:', model.dump(Area([Point(1.11, 2.54), Point(3.1, 2.54), Point(2.1, 0)])))
Dumped: {'points': [['1.11', '2.54'], ['3.10', '2.54'], ['2.10', '0.00']]}
```


[py-json]: https://docs.python.org/3.7/library/json.html#json.load
[py-pickle]: https://docs.python.org/3.7/library/pickle.html#pickle.load
[json-model]: models.md#jsonmodel
[dict-model]: models.md#dictmodel
[model-init-serializers]: models.md#serializers
[iso8601]: https://en.wikipedia.org/wiki/ISO_8601