from __future__ import annotations

from dataclasses import fields, MISSING, Field, is_dataclass
from typing import Generic, Iterable, Type, Dict, Any, Union, Mapping, Optional, Iterator, TypeVar

from serious.descriptors import scan_types, TypeDescriptor
from serious.errors import ModelContainsAny, ModelContainsUnion, MissingField, UnexpectedItem, ValidationError, \
    LoadError, DumpError, FieldMissingSerializer
from serious.checks import check_is_instance
from serious.utils import Dataclass
from serious.validation import validate
from .check_frozen import check_frozen
from .key_mapper import KeyMapper, NoopKeyMapper
from .process import Loading, Dumping
from .serializer import FieldSerializer

T = TypeVar('T')
M = TypeVar('M')  # Python model value
S = TypeVar('S')  # Serialized value


class SeriousModel(Generic[T]):
    """A dataclasses/dict serialization model."""

    def __init__(
            self,
            descriptor: TypeDescriptor,
            serializers: Iterable[Type[FieldSerializer]],
            *,
            allow_any: bool,
            allow_missing: bool,
            allow_unexpected: bool,
            validate_on_load: bool,
            validate_on_dump: bool,
            ensure_frozen: Union[bool, Iterable[Type]],
            key_mapper: Optional[KeyMapper] = None,
            _registry: Dict[TypeDescriptor, SeriousModel] = None
    ):
        """A new model.

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
        assert is_dataclass(descriptor.cls), 'Serious can only operate on dataclasses.'
        all_types = scan_types(descriptor)
        if not allow_any and Any in all_types:
            raise ModelContainsAny(descriptor.cls)
        if Union in all_types:
            raise ModelContainsUnion(descriptor.cls)
        if ensure_frozen:
            check_frozen(descriptor, all_types, ensure_frozen)
        self._descriptor = descriptor
        self._serializers = tuple(serializers)
        self._allow_any = allow_any
        self._allow_missing = allow_missing
        self._allow_unexpected = allow_unexpected
        self._validate_on_load = validate_on_load
        self._validate_on_dump = validate_on_dump
        self._ensure_frozen = ensure_frozen
        self._serializer_registry = {descriptor: self} if _registry is None else _registry
        self._keys = key_mapper or NoopKeyMapper()
        self._serializers_by_field = {name: self.find_serializer(desc) for name, desc in descriptor.fields.items()}

    @property
    def _cls(self) -> Type[T]:
        # A shortcut to root dataclass type.
        return self._descriptor.cls

    def load(self, data: Mapping, _ctx: Optional[Loading] = None) -> T:
        """Loads dataclass from a dictionary or other mapping. """

        check_is_instance(data, Mapping, f'Invalid data for {self._cls}')  # type: ignore
        root = _ctx is None
        loading: Loading
        loading = Loading(validating=self._validate_on_load) if root else _ctx  # type: ignore # checked above
        mut_data = {self._keys.to_model(key): value for key, value in data.items()}
        if self._allow_missing:
            for field in _fields_missing_from(mut_data, self._cls):
                mut_data[field.name] = None
        else:
            _check_for_missing(self._cls, mut_data)
        if not self._allow_unexpected:
            _check_for_unexpected(self._cls, mut_data)
        try:
            init_kwargs = {
                field: loading.run(f'.{self._keys.to_serialized(field)}', serializer, mut_data[field])
                for field, serializer in self._serializers_by_field.items()
                if field in mut_data
            }
            result = self._cls(**init_kwargs)  # type: ignore # not an object
            if self._validate_on_load:
                validate(result)
            return result
        except ValidationError:
            raise
        except Exception as e:
            if root:
                raise LoadError(self._cls, loading.stack, data) from e
            raise

    def dump(self, o: T, _ctx: Optional[Dumping] = None) -> Dict[str, Any]:
        """Dumps a dataclass object to a dictionary."""

        check_is_instance(o, self._cls)
        root = _ctx is None
        dumping: Dumping = Dumping(validating=False) if root else _ctx  # type: ignore # checked above
        try:
            _s = self._keys.to_serialized
            if self._validate_on_dump:
                validate(o)
            return {
                _s(field): dumping.run(f'.{_s(field)}', serializer, getattr(o, field))
                for field, serializer in self._serializers_by_field.items()
            }
        except ValidationError:
            raise
        except Exception as e:
            if root:
                raise DumpError(o, dumping.stack) from e
            raise

    def child_model(self, descriptor: TypeDescriptor) -> SeriousModel:
        """
        Creates a `SeriousModel` for dataclass fields nested in the current serializers.
        The preferences of the nested dataclasses match those of the root one.
        """
        if descriptor == self._descriptor:
            return self
        if descriptor in self._serializer_registry:
            return self._serializer_registry[descriptor]
        new_model: SeriousModel = SeriousModel(
            descriptor=descriptor,
            serializers=self._serializers,
            allow_any=self._allow_any,
            allow_missing=self._allow_missing,
            allow_unexpected=self._allow_unexpected,
            validate_on_load=self._validate_on_load,
            validate_on_dump=self._validate_on_dump,
            ensure_frozen=self._ensure_frozen,
            key_mapper=self._keys,
            _registry=self._serializer_registry
        )
        self._serializer_registry[descriptor] = new_model
        return new_model

    def find_serializer(self, descriptor: TypeDescriptor) -> FieldSerializer:
        """
        Creates a serializer fitting the provided field descriptor.

        :param descriptor: descriptor of a field to serialize.
        """
        serializer = self._find_serializer(descriptor)
        if serializer is None:
            raise FieldMissingSerializer(self._descriptor.cls, descriptor)
        return serializer

    def _find_serializer(self, desc: TypeDescriptor) -> Optional[FieldSerializer]:
        sr_generator = (serializer(desc, self) for serializer in self._serializers if serializer.fits(desc))
        optional_sr = next(sr_generator, None)
        return optional_sr


def _check_for_missing(cls: Type[Dataclass], data: Mapping) -> None:
    """ Checks for missing keys in data that are part of the provided dataclass.
    :raises: MissingField
    """
    missing_fields = filter(lambda f: f.name not in data, fields(cls))
    first_missing_field: Any = next(missing_fields, MISSING)
    if first_missing_field is not MISSING:
        field_names = {first_missing_field.name} | {field.name for field in missing_fields}
        raise MissingField(cls, data, field_names)


def _check_for_unexpected(cls: Type[Dataclass], data: Mapping) -> None:
    """ Checks for keys in data that are not part of the provided dataclass.
    :raises: UnexpectedItem
    """
    field_names = {field.name for field in fields(cls)}
    data_keys = set(data.keys())
    unexpected_fields = data_keys - field_names
    if any(unexpected_fields):
        raise UnexpectedItem(cls, data, unexpected_fields)


def _fields_missing_from(data: Mapping, cls: Type[Dataclass]) -> Iterator[Field]:
    """Fields missing from data, but present in the dataclass."""

    def _is_missing(field: Field) -> bool:
        return field.name not in data \
               and field.default is MISSING \
               and field.default_factory is MISSING  # type: ignore # default factory is an unbound function

    return filter(_is_missing, fields(cls))
