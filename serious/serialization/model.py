"""
`SeriousModel` is the core of Serious implementation traversing the dataclass, checking it’s correctness,
 and serializing it to/from dictionaries of primitives.
"""
from __future__ import annotations

__all__ = ["SeriousModel"]

from dataclasses import fields, MISSING, Field, is_dataclass
from typing import (
    Generic,
    Iterable,
    Type,
    Dict,
    Any,
    Union,
    Mapping,
    Optional,
    Iterator,
    TypeVar,
)

from serious.checks import check_is_instance
from serious.descriptors import scan_types, Descriptor
from serious.errors import (
    ModelContainsAny,
    MissingField,
    UnexpectedItem,
    ValidationError,
    LoadError,
    DumpError,
    MissingSerializer,
)
from serious.utils import Dataclass
from .check_immutable import check_immutable
from .context import SerializationContext
from .key_mapper import KeyMapper, NoopKeyMapper
from .serializer import Serializer

T = TypeVar("T")
M = TypeVar("M")  # Python model value
S = TypeVar("S")  # Serialized value


class SeriousModel(Generic[T]):
    """Serious internal model implementation reused by the exposed models (like JSON/YAML/dict/etc).

    Checks the provided descriptor for model errors when instantiated.

    Used to serialize dataclasses to python dictionaries of primitives.
    Dictionaries of primitives are then transformed to target output formats like JSON by other tools.
    For JSON it’s Python built-in `json` module.
    """

    def __init__(
        self,
        descriptor: Descriptor,
        serializers: Iterable[Type[Serializer]],
        *,
        allow_any: bool,
        allow_missing: bool,
        allow_unexpected: bool,
        validate_on_load: bool,
        validate_on_dump: bool,
        ensure_frozen: Union[bool, Iterable[Type]],
        key_mapper: Optional[KeyMapper] = None,
        _registry: Optional[Dict[Descriptor, SeriousModel]] = None,
    ):
        """Initialize a Serious Model.

        :param descriptor: the descriptor of the dataclass to load/dump.
        :param serializers: field serializer classes in an order they will be tested for fitness for each field.
        :param allow_any: `False` to raise if the model contains fields annotated with `Any`
                    (this includes generics like `List[Any]`, or simply `list`).
        :param allow_missing: `False` to raise during load if data is missing the optional fields.
        :param allow_unexpected: `False` to raise during load if data contains some unknown fields.
        :param validate_on_load: to call dataclass __validate__ method after object construction.
        :param validate_on_load: to call object __validate__ before dumping.
        :param ensure_frozen: `False` to skip check of model immutability; `True` will perform the check
                against built-in immutable types; a list of custom immutable types is added to built-ins.
        :param key_mapper: remap field names of between dataclass and serialized objects.
        :param _registry: a mapping of dataclass type descriptors to corresponding serious serializer;
                used internally to create child serializers.
        """
        assert is_dataclass(descriptor.cls), "Serious can only operate on dataclasses."
        all_types = scan_types(descriptor)
        if not allow_any and Any in all_types:
            raise ModelContainsAny(descriptor.cls)
        if ensure_frozen:
            check_immutable(descriptor, all_types, ensure_frozen)
        self.descriptor = descriptor
        self.serializers = tuple(serializers)
        self.allow_any = allow_any
        self.allow_missing = allow_missing
        self.allow_unexpected = allow_unexpected
        self.validate_on_load = validate_on_load
        self.validate_on_dump = validate_on_dump
        self.ensure_frozen = ensure_frozen
        self.serializer_registry = {descriptor: self} if not _registry else _registry
        self.keys = key_mapper or NoopKeyMapper()
        self.serializers_by_field = {
            name: self.find_serializer(desc) for name, desc in descriptor.fields.items()
        }

    @property
    def cls(self) -> Type[T]:
        # A shortcut to root dataclass type.
        return self.descriptor.cls

    def load(self, data: Mapping, _ctx: Optional[SerializationContext] = None) -> T:
        """Loads dataclass from a dictionary or other mapping."""

        check_is_instance(data, Mapping, f"Invalid data for {self.cls}")  # type: ignore
        if _ctx is None:
            root = True
            ctx = SerializationContext(validating=self.validate_on_load, steps=[(self.cls.__name__, data)])
        else:
            root = False
            ctx = _ctx
        mut_data = {self.keys.to_model(key): value for key, value in data.items()}
        if self.allow_missing:
            for field in fields_missing_from(mut_data, self.cls):
                mut_data[field.name] = None
        else:
            check_for_missing(self.cls, mut_data, ctx)
        if not self.allow_unexpected:
            check_for_unexpected(self.cls, mut_data, ctx)
        try:
            init_kwargs = {
                field: serializer.load_nested(
                    f".{self.keys.to_serialized(field)}", mut_data[field], ctx
                )
                for field, serializer in self.serializers_by_field.items()
                if field in mut_data
            }
            result = self.cls(**init_kwargs)  # type: ignore # not an object
            if self.validate_on_load:
                ctx.validate(result)
            return result
        except ValidationError as e:
            if root:
                raise ValidationError(f"{ctx.failed_validation_at()}: {e}") from e
            raise
        except Exception as e:
            if root:
                raise LoadError(self.cls, ctx, data) from e
            raise

    def dump(self, o: T, _ctx: Optional[SerializationContext] = None) -> Dict[str, Any]:
        """Dumps a dataclass object to a dictionary."""

        check_is_instance(o, self.cls)
        if _ctx is None:
            root = True
            ctx = SerializationContext(validating=False, steps=[(self.cls.__name__, o)])
        else:
            root = False
            ctx = _ctx
        try:
            _s = self.keys.to_serialized
            result = {
                _s(field): serializer.dump_nested(
                    f".{_s(field)}", getattr(o, field), ctx
                )
                for field, serializer in self.serializers_by_field.items()
            }
            if self.validate_on_dump:
                ctx.validate(self.load(result, ctx))
            return result
        except ValidationError as e:
            if root:
                raise ValidationError(f"{ctx.failed_validation_at()}: {e}") from e
            raise
        except Exception as e:
            if root:
                raise DumpError(o, ctx) from e
            raise

    def child_model(self, descriptor: Descriptor) -> SeriousModel:
        """
        Creates a `SeriousModel` for dataclass fields nested in the current serializers.
        The preferences of the nested dataclasses match those of the root one.
        """
        if descriptor == self.descriptor:
            return self
        if descriptor in self.serializer_registry:
            return self.serializer_registry[descriptor]
        new_model: SeriousModel = SeriousModel(
            descriptor=descriptor,
            serializers=self.serializers,
            allow_any=self.allow_any,
            allow_missing=self.allow_missing,
            allow_unexpected=self.allow_unexpected,
            validate_on_load=self.validate_on_load,
            validate_on_dump=self.validate_on_dump,
            ensure_frozen=self.ensure_frozen,
            key_mapper=self.keys,
            _registry=self.serializer_registry,
        )
        self.serializer_registry[descriptor] = new_model
        return new_model

    def find_serializer(self, descriptor: Descriptor) -> Serializer:
        """
        Creates a serializer fitting the provided field descriptor.

        :param descriptor: descriptor of a field to serialize.
        """
        for serializer in self.serializers:
            if serializer.fits(descriptor):
                return serializer(descriptor, self)
        raise MissingSerializer(self.descriptor.cls, descriptor)


def check_for_missing(cls: Type[Dataclass], data: Mapping, ctx: SerializationContext) -> None:
    """Checks for missing keys in data that are part of the provided dataclass.
    :raises: MissingField
    """
    missing_fields = filter(lambda f: f.name not in data, fields(cls))
    first_missing_field: Any = next(missing_fields, MISSING)
    if first_missing_field is not MISSING:
        field_names = {first_missing_field.name} | {
            field.name for field in missing_fields
        }
        raise MissingField(cls, data, field_names, ctx)


def check_for_unexpected(cls: Type[Dataclass], data: Mapping, ctx: SerializationContext) -> None:
    """Checks for keys in data that are not part of the provided dataclass.
    :raises: UnexpectedItem
    """
    field_names = {field.name for field in fields(cls)}
    data_keys = set(data.keys())
    unexpected_fields = data_keys - field_names
    if any(unexpected_fields):
        raise UnexpectedItem(cls, data, unexpected_fields, ctx)


def fields_missing_from(data: Mapping, cls: Type[Dataclass]) -> Iterator[Field]:
    """Fields missing from data, but present in the dataclass."""

    def _is_missing(field: Field) -> bool:
        return (
            field.name not in data
            and field.default is MISSING
            and field.default_factory is MISSING
        )  # type: ignore # default factory is an unbound function

    return filter(_is_missing, fields(cls))
