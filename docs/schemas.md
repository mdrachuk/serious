# Schemas
Schema is the entry point to Serious. You create it to serialize data and validate created objects.
Schema is the thing doing heavy lifting in Serious. 
Upon creation a Schema:

- builds a hierarchy of descriptors unwrapping the generics, optionals, etc;
- checks that this model conforms to your requirements;
- forms a tree of serializers to executed upon load/dump.

There are two schema types at this point:

1. [`JsonSchema` for working with JSON strings](#jsonschema)
2. [`DictSchema` for working with Python dictionaries](#dictschema)

Schema protocol is defined by 5 methods:

- `__init__(cls: Type[T], **options)` — a constructor from a dataclass type and implementation specific options.
- `load(data: D) -> T` — create a new dataclass instance from a schema-specific encoded data.
- `dump(obj: T) -> D` — encode a dataclass to schema-specific type.
- `load_many(data: DC) -> FrozenList[T]` — load a list of dataclass instances from data.
- `dump_many(obj: Iterable[T]) -> DC` — dump multiple objects at once.

## JsonSchema
### `__init__` 
```python
def __init__(
        self,
        cls: Type[T],
        *,
        serializers: Iterable[Type[FieldSerializer]] = field_serializers(),
        allow_any: bool = False,
        allow_missing: bool = False,
        allow_unexpected: bool = False,
        indent: Optional[int] = None
)
```
- `cls` the descriptor of the dataclass to load/dump.
- `serializers` field serializer classes in an order they will be tested for fitness for each field.
        @param allow_any False to raise if the model contains fields annotated with Any
                (this includes generics like List[Any], or simply list).
        @param allow_missing False to raise during load if data is missing the optional fields.
        @param allow_unexpected False to raise during load if data is missing the contains some unknown fields.
        @param indent number of spaces JSON output will be indented by; `None` for most compact representation.


## DictSchema