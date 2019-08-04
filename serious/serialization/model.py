from __future__ import annotations

from dataclasses import fields, MISSING, Field
from typing import Generic, Iterable, Type, Dict, Any, Union, Mapping, Optional, Iterator, TypeVar

from serious.descriptors import scan_types, TypeDescriptor
from serious.errors import ModelContainsAny, ModelContainsUnion, MissingField, UnexpectedItem, ValidationError, \
    LoadError, DumpError
from serious.preconditions import _check_is_dataclass, _check_is_instance, _check_present
from serious.utils import DataclassType
from serious.validation import validate
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
            _registry: Dict[TypeDescriptor, SeriousModel] = None
    ):
        """
        @param descriptor the descriptor of the dataclass to load/dump.
        @param serializers field serializer classes in an order they will be tested for fitness for each field.
        @param allow_any `False` to raise if the model contains fields annotated with `Any`
                (this includes generics like `List[Any]`, or simply `list`).
        @param allow_missing `False` to raise during load if data is missing the optional fields.
        @param allow_unexpected `False` to raise during load if data contains some unknown fields.
        @param _registry a mapping of dataclass type descriptors to corresponding serious serializer;
                used internally to create child serializers.
        """
        _check_is_dataclass(descriptor.cls, 'Serious can only operate on dataclasses.')
        all_types = scan_types(descriptor)
        if not allow_any and Any in all_types:
            raise ModelContainsAny(descriptor.cls)
        if Union in all_types:
            raise ModelContainsUnion(descriptor.cls)
        self._descriptor = descriptor
        self._serializers = tuple(serializers)
        self._allow_missing = allow_missing
        self._allow_unexpected = allow_unexpected
        self._allow_any = allow_any
        self._serializer_registry = {descriptor: self} if _registry is None else _registry
        self._field_serializers = {name: self.find_serializer(desc) for name, desc in descriptor.fields.items()}

    @property
    def _cls(self) -> Type[T]:
        # A shortcut to root dataclass type.
        return self._descriptor.cls

    def load(self, data: Mapping, _ctx: Optional[Loading] = None) -> T:
        """Loads dataclass from a dictionary or other mapping. """

        _check_is_instance(data, Mapping, f'Invalid data for {self._cls}')  # type: ignore
        root = _ctx is None
        loading: Loading = Loading() if root else _ctx  # type: ignore # checked above
        mut_data = dict(data)
        if self._allow_missing:
            for field in _fields_missing_from(mut_data, self._cls):
                mut_data[field.name] = None
        else:
            _check_for_missing(self._cls, mut_data)
        if not self._allow_unexpected:
            _check_for_unexpected(self._cls, mut_data)
        try:
            init_kwargs = {
                field: loading.run(f'.[{field}]', serializer, mut_data[field])
                for field, serializer in self._field_serializers.items()
                if field in mut_data
            }
            result = self._cls(**init_kwargs)  # type: ignore # not an object
            validate(result)
            return result
        except Exception as e:
            if root:
                if isinstance(e, ValidationError):
                    raise
                else:
                    raise LoadError(self._cls, loading.stack, data) from e
            raise

    def dump(self, o: T, _ctx: Optional[Dumping] = None) -> Dict[str, Any]:
        """Dumps a dataclass object to a dictionary."""

        _check_is_instance(o, self._cls)
        root = _ctx is None
        dumping: Dumping = Dumping() if root else _ctx  # type: ignore # checked above
        try:
            return {
                field: dumping.run(f'.[{field}]', serializer, getattr(o, field))
                for field, serializer in self._field_serializers.items()
            }
        except Exception as e:
            if root:
                raise DumpError(o, dumping.stack) from e
            raise

    def child_model(self, descriptor: TypeDescriptor) -> SeriousModel:
        """
        Creates a [SeriousModel] for dataclass fields nested in the current serializers.
        The preferences of the nested dataclasses match those of the root one.
        """

        if descriptor in self._serializer_registry:
            return self._serializer_registry[descriptor]
        new_model: SeriousModel = SeriousModel(
            descriptor=descriptor,
            serializers=self._serializers,
            allow_missing=self._allow_missing,
            allow_unexpected=self._allow_unexpected,
            allow_any=self._allow_any,
            _registry=self._serializer_registry
        )
        self._serializer_registry[descriptor] = new_model
        return new_model

    def find_serializer(self, descriptor: TypeDescriptor) -> FieldSerializer:
        """
        Creates a serializer fitting the provided field descriptor.

        @param descriptor descriptor of a field to serialize.
        """
        optional = self._find_serializer(descriptor)
        serializer = _check_present(optional, f'Type "{descriptor.cls}" is not supported')
        return serializer

    def _find_serializer(self, desc: TypeDescriptor) -> Optional[FieldSerializer]:
        sr_generator = (serializer(desc, self) for serializer in self._serializers if serializer.fits(desc))
        optional_sr = next(sr_generator, None)
        return optional_sr


def _check_for_missing(cls: DataclassType, data: Mapping) -> None:
    """
    Checks for missing keys in data that are part of the provided dataclass.

    @raises MissingField
    """
    missing_fields = filter(lambda f: f.name not in data, fields(cls))
    first_missing_field: Any = next(missing_fields, MISSING)
    if first_missing_field is not MISSING:
        field_names = {first_missing_field.name} | {field.name for field in missing_fields}
        raise MissingField(cls, data, field_names)


def _check_for_unexpected(cls: DataclassType, data: Mapping) -> None:
    """
    Checks for keys in data that are not part of the provided dataclass.

    @raises UnexpectedItem
    """
    field_names = {field.name for field in fields(cls)}
    data_keys = set(data.keys())
    unexpected_fields = data_keys - field_names
    if any(unexpected_fields):
        raise UnexpectedItem(cls, data, unexpected_fields)


def _fields_missing_from(data: Mapping, cls: DataclassType) -> Iterator[Field]:
    """Fields missing from data, but present in the dataclass."""

    def _is_missing(field: Field) -> bool:
        return field.name not in data \
               and field.default is MISSING \
               and field.default_factory is MISSING  # type: ignore # default factory is an unbound function

    return filter(_is_missing, fields(cls))
