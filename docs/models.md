Model is the entry point to Serious. You create it to serialize data and validate created objects. 
When does multiple things upon creation:

- builds a hierarchy of descriptors unwrapping the generics, optionals, etc;
- checks that this model conforms to your requirements;
- forms a tree of serializers to executed upon load/dump.

There are two model types at this point:

1. [`JsonModel` for working with JSON strings](#jsonmodel)
2. [`DictModel` for working with Python dictionaries](#dictmodel)


## Protocol
Model protocol is defined by 5 methods.

<dl>
    <dt><code>def __init__(cls: Type[T], *, **options):</code></dt>
    <dd>A constructor from a dataclass type and implementation specific options.</dd>

    <dt><code>def load(data: D) -> T:</code></dt>
    <dd>Create a new dataclass instance from a model-specific encoded data.</dd>

    <dt><code>def dump(obj: T) -> D:</code></dt>
    <dd>Encode a dataclass to model-specific type.</dd>

    <dt><code>def load_many(data: DC) -> List[T]:</code></dt>
    <dd>Load a list of dataclass instances from model-specific encoded data collection.</dd>

    <dt><code>def dump_many(obj: Iterable[T]) -> DC:</code></dt>
    <dd>Dump multiple objects at once to model-specific collection.</dd>
</dl>

## Common Options

### `serializers`
_Type:_ `Iterable[Type[FieldSerializer]]` 
_Default:_ `serious.serialization.field_serializers()` 

An ordered collection of field serializer classes. Pass a non-default collection to override how particular fields are
serialized by the model. For more refer to [custom serialization guide][custom-serialization].

### `allow_any`
_Type:_ `bool`
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
>>> JsonModel(Message, allow_any=False)
Traceback (most recent call last):
  File "<input>", line 1, in <module>
  File ".../serious/json/api.py", line 42, in __init__
    allow_unexpected=allow_unexpected,
  File ".../serious/serialization.py", line 729, in __init__
    raise ModelContainsAny(descriptor.cls)
serious.errors.ModelContainsAny: <class '__main__.Message'>
```


You can pass `allow_any=True` to model to serialize load/dump `Any` fields as is, 
although this can lead to uncertain behaviour.

  
### `allow_missing`
_Type:_ `bool`
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

Then loading JSON to a model with `allow_missing=True` without `height` will set it to None:
```python
>>> JsonModel(Dinosaur, allow_missing=True).load('{"name": "Yoshi"}')
Dinosaur(name='Yoshi', height=None)
```  
### `allow_unexpected`
_Type:_ `bool`
_Default:_ `False` 

If there will be some redundant data serious default is to error. The idea here is to fail fast. 
But if you would like to just skip extra fields, then pass `allow_unexpected=True` to your model:
```python
>>> JsonModel(Dinosaur, allow_unexpected=True).load('{"name": "Yoshi", "height": null, "clothing": "orange boots"}')
Dinosaur(name='Yoshi', height=None)
```   
## JsonModel
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
    <dt><code>def load(self, json_: str) -> T:</code></dt>
    <dd>Creates an instance of dataclass from a JSON string.</dd>
    <dt><code>def dump(self, o: Any) -> str:</code></dt>
    <dd>Dumps an instance of dataclass to a JSON string.</dd>
    <dt><code>def load_many(self, json_: str) -> List[T]:</code></dt>
    <dd>Loads multiple <code>T</code> dataclass objects from JSON array of objects string.</dd>
    <dt><code>def dump_many(self, items: Collection[T]) -> str:</code></dt>
    <dd>Dumps a list/set/collection of objects to an array of objects JSON string.</dd>
</dl>

## DictModel

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
    <dt><code>def load(self, data: Dict[str, Any]) -> T:</code></dt>
    <dd>Creates an instance of <code>T</code> from a dictionary with string keys.</dd>
    <dt><code>def dump(self, o: Any) -> Dict[str, Any]</code></dt>
    <dd>Dumps an instance of dataclass to a Python dictionary.</dd>
    <dt><code>def load_many(self, items: Iterable[Dict[str, Any]]) -> List[T]:</code></dt>
    <dd>Loads multiple <code>T</code> dataclass objects from a list of dictionaries.</dd>
    <dt><code>def dump_many(self, items: Collection[T]) -> List[Dict[str, Any]]:</code></dt>
    <dd>Dumps a list/set/collection of objects to an list of primitive dictionaries.</dd>
</dl>


## Custom Model
Models do not share any common parent class. 
Instead the idea is: _"If it walks like a duck and it quacks like a duck, then it must be a duck"_.

So what you should do is implement the [protocol described above](#protocol).

Internally, your model will need to create a descriptor of your dataclass, specifying fields types and modifiers.
A root dataclass `TypeDescriptor` is created by `serious.descriptors.describe` function. 

Having a descriptor in place, `serious.serialization.SeriousModel` may be helpful. 
`SeriousModel` forms a tree of field serializers executed upon load and dump operations.
It does so from the provided descriptor and a list of all possible [field serializers][field-serializers].

Check [implementation][implementation] for more details on how existing code base works 
and [check sources for JsonModel][json-model-src] for a comprehensive example:

```python
class JsonModel(Generic[T]):

    def __init__(
            self,
            cls: Type[T],
            *,
            serializers: Iterable[Type[FieldSerializer]] = field_serializers(),
            allow_any: bool = False,
            allow_missing: bool = False,
            allow_unexpected: bool = False,
            indent: Optional[int] = None,
    ):
        self._descriptor = describe(cls)
        self._serializer = SeriousModel(
            self.descriptor,
            serializers,
            allow_any=allow_any,
            allow_missing=allow_missing,
            allow_unexpected=allow_unexpected,
        )
        self._dump_indentation = indent

    @property
    def cls(self):
        return self._descriptor.cls

    def load(self, json_: str) -> T:
        data: MutableMapping = self._load_from_str(json_)
        _check_that_loading_an_object(data, self.cls)
        return self._from_dict(data)

    def load_many(self, json_: str) -> List[T]:
        data: Collection = self._load_from_str(json_)
        _check_that_loading_a_list(data, self.cls)
        return [self._from_dict(each) for each in data]

    def dump(self, o: T) -> str:
        _check_is_instance(o, self.cls)
        return self._dump_to_str(self._serializer.dump(o))

    def dump_many(self, items: Collection[T]) -> str:
        dict_items = list(map(self._dump, items))
        return self._dump_to_str(dict_items)

    def _dump(self, o) -> Dict[str, Any]:
        return self._serializer.dump(_check_is_instance(o, self.cls))

    def _from_dict(self, data: MutableMapping) -> T:
        return self._serializer.load(data)

    def _load_from_str(self, json_: str) -> Any:
        """Override to customize JSON loading behaviour."""
        return json.loads(json_)

    def _dump_to_str(self, dict_items: Any) -> str:
        """Override to customize JSON dumping behaviour."""
        return json.dumps(dict_items,
                          skipkeys=False,
                          ensure_ascii=False,
                          check_circular=True,
                          allow_nan=False,
                          indent=self._dump_indentation,
                          separators=None,
                          default=None,
                          sort_keys=False)

```

[json-model-src]: https://github.com/mdrachuk/serious/blob/master/serious/json/api.py 
[field-serializers]: serialization.md#field-serializers 
[custom-serialization]: serialization.md#custom-field-serializers 
[implementation]: implementation.md 
   