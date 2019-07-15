from __future__ import annotations

from dataclasses import fields, MISSING, Field
from typing import Mapping, Type, Any, Dict, Iterator, Generic, TypeVar, Optional, Iterable

from serious.context import SerializationContext
from serious.descriptors import FieldDescriptor, TypeDescriptor, _contains_any
from serious.errors import LoadError, DumpError, UnexpectedItem, MissingField, ModelContainsAny
from serious.field_serializers import FieldSerializer
from serious.preconditions import _check_present, _check_is_instance
from serious.utils import DataclassType

T = TypeVar('T')


class SeriousSchema(Generic[T]):
    """A serializer for dataclasses from and to a dict."""

    def __init__(
            self,
            descriptor: TypeDescriptor[T],
            serializers: Iterable[Type[FieldSerializer]],
            *,
            allow_any: bool,
            allow_missing: bool,
            allow_unexpected: bool,
            _registry: Dict[TypeDescriptor, SeriousSchema] = None
    ):
        """
        @param descriptor the descriptor of the dataclass to load/dump.
        @param serializers field serializer classes in an order they will be tested for fitness for each field.
        @param allow_any False to raise if the model contains fields annotated with Any
                (this includes generics like List[Any], or simply list).
        @param allow_missing False to raise during load if data is missing the optional fields.
        @param allow_unexpected False to raise during load if data is missing the contains some unknown fields.
        @param _registry a mapping of dataclass type descriptors to corresponding serious serializer;
                used internally to create child serializers.
        """
        if not allow_any and _contains_any(descriptor):
            raise ModelContainsAny(descriptor.cls)
        self._descriptor = descriptor
        self._serializers = tuple(serializers)
        self._allow_missing = allow_missing
        self._allow_unexpected = allow_unexpected
        self._allow_any = allow_any
        self._serializer_registry = {descriptor: self} if _registry is None else _registry
        self._field_serializers = [self.field_serializer(field) for field in descriptor.fields]

    @property
    def _cls(self) -> Type[T]:
        # A shortcut to root dataclass type.
        return self._descriptor.cls

    def child_serializer(self, field: FieldDescriptor) -> SeriousSchema:
        """Creates a [SeriousSchema] for dataclass fields nested in the current serializers.
        The preferences of the nested dataclasses match those of the root one.
        """

        descriptor = field.type
        if descriptor in self._serializer_registry:
            return self._serializer_registry[descriptor]
        new_serializer = SeriousSchema(
            descriptor=descriptor,
            serializers=self._serializers,
            allow_missing=self._allow_missing,
            allow_unexpected=self._allow_unexpected,
            allow_any=self._allow_any,
            _registry=self._serializer_registry
        )
        self._serializer_registry[descriptor] = new_serializer
        return new_serializer

    def load(self, data: Mapping, _ctx: Optional[SerializationContext] = None) -> T:
        """Loads dataclass from a dictionary or other mapping. """

        _check_is_instance(data, Mapping, f'Invalid data for {self._cls}')  # type: ignore
        root = _ctx is None
        ctx: SerializationContext = SerializationContext() if root else _ctx  # type: ignore # checked above
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
                serializer.field.name: self._load_field(mut_data, serializer, ctx)
                for serializer in self._field_serializers
                if serializer.field.name in mut_data
            }
            return self._cls(**init_kwargs)  # type: ignore # not an object
        except Exception as e:
            if root:
                raise LoadError(self._cls, ctx.stack, data) from e
            raise

    @staticmethod
    def _load_field(data: Mapping[str, Any], serializer: FieldSerializer, ctx: SerializationContext) -> Any:
        field = serializer.field
        with ctx.enter(serializer):
            return serializer.load(data[field.name], ctx)

    def dump(self, o: T, _ctx: Optional[SerializationContext] = None) -> Dict[str, Any]:
        """Dumps a dataclass object to a dictionary."""

        _check_is_instance(o, self._cls)
        root = _ctx is None
        ctx: SerializationContext = SerializationContext() if root else _ctx  # type: ignore # checked above
        try:
            return {
                serializer.field.name: self._dump_field(o, serializer, ctx)
                for serializer in self._field_serializers
            }
        except Exception as e:
            if root:
                raise DumpError(o, ctx.stack) from e
            raise

    @staticmethod
    def _dump_field(o: Any, serializer: FieldSerializer, ctx: SerializationContext) -> Any:
        field = serializer.field
        with ctx.enter(serializer):
            return serializer.dump(getattr(o, field.name), ctx)

    def field_serializer(self, field: FieldDescriptor) -> FieldSerializer:
        """
        Creates a serializer fitting the provided field descriptor.

        @param field descriptor of a field to serialize.
        """
        optional = self._get_serializer(field)
        serializer = _check_present(optional, f'Type "{field.type.cls}" is not supported')
        return serializer

    def _get_serializer(self, field: FieldDescriptor) -> Optional[FieldSerializer]:
        sr_generator = (serializer(field, self) for serializer in self._serializers if serializer.fits(field))
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
