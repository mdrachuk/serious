# Schemas
Schema is the entry point to Serious. You create it to serialize data and validate created objects. 
When it is created it:

- builds a hierarchy of descriptors unwrapping the generics, optionals, etc;
- checks that this model conforms to your requirements;
- forms a tree of serializers to executed upon load/dump.

There are two schema types at this point:

1. [`JsonSchema` for working with JSON strings](#jsonschema)
2. [`DictSchema` for working with Python dictionaries](#dictschema)


## Protocol
Schema protocol is defined by 5 methods.

<dl>
    <dt><code>def __init__(cls: Type[T], *, **options):</code></dt>
    <dd>A constructor from a dataclass type and implementation specific options.</dd>
</dl>

<dl>
    <dt><code>def load(data: D) -> T:</code></dt>
    <dd>Create a new dataclass instance from a schema-specific encoded data.</dd>
</dl>

<dl>
    <dt><code>def dump(obj: T) -> D:</code></dt>
    <dd>Encode a dataclass to schema-specific type.</dd>
</dl>

<dl>
    <dt><code>def load_many(data: DC) -> List[T]:</code></dt>
    <dd>Load a list of dataclass instances from schema-specific encoded data collection.</dd>
</dl>

<dl>
    <dt><code>def dump_many(obj: Iterable[T]) -> DC:</code></dt>
    <dd>Dump multiple objects at once to schema-specific collection.</dd>
</dl>

## Common Options

### `serializers: Iterable[Type[FieldSerializer]]`
_Default:_ `serious.serialization.field_serializers()` 

An ordered collection of field serializer classes. Pass a non-default collection to override how particular fields are
serialized by the schema. For more refer to [custom serialization guide](/serialization#custom)

### `allow_any: bool`
_Default:_ `False`
 
By default the dataclass and its fields cannot contain unambiguous fields annotated with `Any`. 
This also includes generics like `list` which is equal to `List[Any]`.

Both examples below are ambiguous in this manner:
```python
@dataclass
class User:
    metadata: dict

@dataclass
class Message:
    extras: Any
```

Loading them will result in error:
```python
>>> JsonSchema(Message, allow_any=False)
Traceback (most recent call last):
  File "<input>", line 1, in <module>
  File ".../serious/json/api.py", line 42, in __init__
    allow_unexpected=allow_unexpected,
  File ".../serious/serialization.py", line 729, in __init__
    raise ModelContainsAny(descriptor.cls)
serious.errors.ModelContainsAny: <class '__main__.Message'>
```


You can pass `allow_any=True` to schema to serialize load/dump `Any` fields as is, 
although this can lead to uncertain behaviour.

  
### `allow_missing: bool`
_Default:_ `False`

By default serious is strict in respect to missing data. A `LoadError` will be raised if some field exists in dataclass 
but is missing from loaded the data.

But some APIs prefer to omit `null` values. To handle such use-case the fields should be marked `Optional`:   
```python
@dataclass
class Dinosaur:
    name: str 
    height: Optional[int] 
```

Then loading JSON to a schema with `allow_missing=True` without `height` will set it to None:
```python
>>> JsonSchema(Dinosaur, allow_missing=True).load('{"name": "Yoshi"}')
Dinosaur(name='Yoshi', height=None)
```  
### `allow_unexpected: bool`
_Default:_ `False` 

If there will be some redundant data serious default is to error. The idea here is to fail fast. 
But if you would like to just skip extra fields, then pass `allow_unexpected=True` to your schema:
```python
>>> JsonSchema(Dinosaur, allow_unexpected=True).load('{"name": "Yoshi", "height": null, "clothing": "orange boots"}')
Dinosaur(name='Yoshi', height=None)
```   
## JsonSchema
<dl>
    <dt><pre>def \_\_init\_\_(
    self,
    cls: Type[T],
    *,
    serializers: Iterable[Type[FieldSerializer]] = field_serializers(),
    allow_any: bool = False,
    allow_missing: bool = False,
    allow_unexpected: bool = False,
    indent: Optional[int] = None,
):</pre></dt>
    <dd><ul>
        <li><code>cls</code> — the descriptor of the dataclass to load/dump.</li>
        <li><code>serializers</code> — field serializer classes in an order they will be tested for fitness for each field.</li>
        <li><code>allow_any</code> — <code>False</code> to raise if the model contains fields annotated with <code>Any</code> (this includes generics like <code>List[Any]</code>, or simply <code>list</code>).</li>
        <li><code>allow_missing</code> — <code>False</code> to raise during load if data is missing the optional fields.</li>
        <li><code>allow_unexpected</code> — <code>False</code> to raise during load if data contains some unknown fields.</li>
        <li><code>indent</code> — number of spaces JSON output will be indented by; `None` for most compact representation.</li>   
     </ul></dd>
</dl>

<dl>
    <dt><code>def load(self, json_: str) -> T:</code></dt>
    <dd>Creates an instance of dataclass from a JSON string.</dd>
</dl>

<dl>
    <dt><code>def dump(self, o: Any) -> str:</code></dt>
    <dd>Dumps an instance of dataclass to a JSON string.</dd>
</dl>

<dl>
    <dt><code>def load_many(self, json_: str) -> List[T]:</code></dt>
    <dd>Loads multiple <code>T</code> dataclass objects from JSON array of objects string.</dd>
</dl>

<dl>
    <dt><code>def dump_many(self, items: Collection[T]) -> str:</code></dt>
    <dd>Dumps a list/set/collection of objects to an array of objects JSON string.</dd>
</dl>

## DictSchema

<dl>
    <dt><pre>def __init__(
    self,
    cls: Type[T],
    *,
    serializers: Iterable[Type[FieldSerializer]] = field_serializers(),
    allow_any: bool = False,
    allow_missing: bool = False,
    allow_unexpected: bool = False,
):</pre></dt>
    <dd><ul>
        <li><code>cls</code> — the descriptor of the dataclass to load/dump.</li>
        <li><code>serializers</code> — field serializer classes in an order they will be tested for fitness for each field.</li>
        <li><code>allow_any</code> — <code>False</code> to raise if the model contains fields annotated with <code>Any</code> (this includes generics like <code>List[Any]</code>, or simply <code>list</code>).</li>
        <li><code>allow_missing</code> — <code>False</code> to raise during load if data is missing the optional fields.</li>
        <li><code>allow_unexpected</code> — <code>False</code> to raise during load if data contains some unknown fields.</li>
     </ul></dd>
</dl>

<dl>
    <dt><code>def load(self, data: Dict[str, Any]) -> T:</code></dt>
    <dd>Creates an instance of <code>T</code> from a dictionary with string keys.</dd>
</dl>

<dl>
    <dt><code>def dump(self, o: Any) -> Dict[str, Any]</code></dt>
    <dd>Dumps an instance of dataclass to a Python dictionary.</dd>
</dl>

<dl>
    <dt><code>def load_many(self, items: Iterable[Dict[str, Any]]) -> List[T]:</code></dt>
    <dd>Loads multiple <code>T</code> dataclass objects a list of dictionaries.</dd>
</dl>

<dl>
    <dt><code>def dump_many(self, items: Collection[T]) -> List[Dict[str, Any]]:</code></dt>
    <dd>Dumps a list/set/collection of objects to an list of primitive dictionaries.</dd>
</dl>