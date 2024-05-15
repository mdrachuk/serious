"""Errors raised by serious.

Errors are divided into 3 main groups:

1. Validation errors -- raised by serious or library users if an objects fails validation.
Contains the stack pointing to an object which raised the error.
2. Serialization errors -- wrap the exceptions which occur during serialization.
They also contain the stack pointing to a specific place which raised the error.
Can be one of `LoadError` or `DumpError`.
3. Model errors -- raised when traversing the dataclass and building the model.
When no serializer found for field, etc.
"""
from __future__ import annotations

__all__ = [
    'SerializationError',
    'LoadError',
    'DumpError',
    'UnexpectedItem',
    'MissingField',
    'ModelError',
    'FieldMissingSerializer',
    'ModelContainsAny',
    'MutableTypesInModel',
    'ValidationError',
]

from typing import Type, Mapping, Collection, TYPE_CHECKING, Iterable

from .utils import class_path, Dataclass

if TYPE_CHECKING:
    from .serialization.context import SerializationStep
    from .descriptors import TypeDescriptor


class SerializationError(Exception):
    """Base for any non-validation error during load or dump."""

    def __init__(self, cls: Type, serializer_stack: Collection[SerializationStep]):
        super().__init__()
        self.cls = cls
        self._path = self.__parse_stack(serializer_stack)

    @staticmethod
    def __parse_stack(serializer_stack: Collection[SerializationStep]) -> str:
        if len(serializer_stack) == 0:
            return ''
        return ''.join(serializer_stack)[1:]

    @property
    def message(self):
        return f'Error during serialization of "{self.cls}"'

    def __str__(self):
        exc_type = super().__str__()
        return f'{exc_type}: {self.message}'


class LoadError(SerializationError):
    """Non-validation error during construction of a dataclass instance from external data.

    This will wrap any error during load process.
    Either invalid data is supplied, or the serializers are handling data incorrectly.
    """

    def __init__(self, cls: Type, serializer_stack: Collection[SerializationStep], data: Mapping):
        super().__init__(cls, serializer_stack)
        self._data = data

    @property
    def message(self):
        return f'Failed to load "{self._path}" of {class_path(self.cls)}: {self.__cause__}. Data: {self._data}'


class DumpError(SerializationError):
    """Non-validation error during encoding of a dataclass instance.

    This error will wrap any error during dump and signifies that
    an invalid dataclass object got into serializers hands or serializers behave incorrectly.
    """

    def __init__(self, obj: Dataclass, serializer_stack: Collection[SerializationStep]):
        super().__init__(type(obj), serializer_stack)
        self._object = obj

    @property
    def message(self):
        return f'Failed to dump "{self._path}" of {self._object}: {self.__cause__}'


class UnexpectedItem(LoadError):

    def __init__(self, cls: Type[Dataclass], data, fields: Collection[str]):
        super().__init__(cls, [], data)
        self._fields = fields

    @property
    def message(self):
        if len(self._fields) == 1:
            field = next(iter(self._fields))
            return f'Unexpected field "{field}" in loaded {class_path(self.cls)}'
        else:
            return f'Unexpected fields {self._fields} in loaded {class_path(self.cls)}'


class MissingField(LoadError):

    def __init__(self, cls: Type[Dataclass], data, fields: Collection[str]):
        super().__init__(cls, [], data)
        self._fields = fields

    @property
    def message(self):
        if len(self._fields) == 1:
            field = next(iter(self._fields))
            return f'Missing field "{field}" in loaded {class_path(self.cls)}'
        else:
            return f'Missing fields {self._fields} in loaded {class_path(self.cls)}'


class ModelError(Exception):
    """An error that can occur when traversing class structure.

    Library and the user can place restrictions on what the model can be.
    This would include containing Any, model mutability, etc.
    Instances of this error will be raised during model construction if such restrictions are unsatisfied.
    """

    def __init__(self, cls: Type):
        self.cls = cls

    @property
    def message(self):
        return f'Model error in class "{self.cls}ю"'


class FieldMissingSerializer(ModelError):

    def __init__(self, cls: Type, desc: TypeDescriptor):
        super().__init__(cls)
        self.desc = desc

    @property
    def message(self):
        return (f'{class_path(self.cls)} contains unserializable member: {self.desc}.'
                f'Create a serializer fitting the descriptor and pass it to the model ``serializers``.')


class ModelContainsAny(ModelError):

    @property
    def message(self):
        return (f'{class_path(self.cls)} contains fields annotated as Any or missing type annotation. '
                f'Provide a type annotation or pass `allow_any=True` to the serializer. '
                f'This may also be an ambiguous ``Generic`` definitions like `x: list`, `x: List` '
                f'which are resolved as `List[Any]`. ')


class MutableTypesInModel(ModelError):

    def __init__(self, cls: Type, mutable_types: Iterable[Type]):
        super().__init__(cls)
        self.mutable_types = mutable_types

    @property
    def message(self):
        return (f'{class_path(self.cls)} is has mutable members: {self.mutable_types}.'
                f'If there are immutable types pass them to model as `ensure_frozen=[Type1, Type2]`.'
                f'Replace mutable types with frozen ones. '
                f'Set @dataclass(frozen=True). \n'
                f'Alternatively, allow mutable fields by passing `ensure_frozen=False` to model. ')


class ValidationError(Exception):
    """An error manifesting an invalid object state.

    Raised when calling `validate(obj)` and internally by serious during load/dump.

    Contains the stack pointing to an exact point where validation failed in data structure.
    """

    def __init__(self, message='Failed validation'):
        super().__init__(message)
