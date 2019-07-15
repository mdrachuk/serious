from typing import Type, Mapping, Collection

from serious.context import SerializationStep
from serious.utils import DataclassType, class_path


class SerializationError(Exception):
    def __init__(self, cls: Type[DataclassType], serializer_stack: Collection[SerializationStep]):
        super().__init__()
        self._cls = cls
        self._path = self.__parse_stack(serializer_stack)

    @staticmethod
    def __parse_stack(serializer_stack: Collection[SerializationStep]) -> str:
        if len(serializer_stack) == 0:
            return ''
        return ''.join(step.step_name() for step in serializer_stack)[1:]

    @property
    def message(self):
        return f'Error during serialization of "{self._cls}"'

    def __str__(self):
        exc_type = super().__str__()
        return f'{exc_type}: {self.message}'


class LoadError(SerializationError):
    def __init__(self, cls: DataclassType, serializer_stack: Collection[SerializationStep], data: Mapping):
        super().__init__(cls, serializer_stack)
        self._data = data

    @property
    def message(self):
        return f'Failed to load "{self._path}" of {class_path(self._cls)} from {self._data}: {self.__cause__}'


class DumpError(SerializationError):
    def __init__(self, obj: DataclassType, serializer_stack: Collection[SerializationStep]):
        super().__init__(type(obj), serializer_stack)
        self._object = obj

    @property
    def message(self):
        return f'Failed to dump "{self._path}" of {self._object}: {self.__cause__}'


class UnexpectedItem(LoadError):
    def __init__(self, cls: Type[DataclassType], data, fields: Collection[str]):
        super().__init__(cls, [], data)
        self._fields = fields

    @property
    def message(self):
        if len(self._fields) == 1:
            field = next(iter(self._fields))
            return f'Unexpected field "{field}" in loaded {class_path(self._cls)}'
        else:
            return f'Unexpected fields {self._fields} in loaded {class_path(self._cls)}'


class MissingField(LoadError):
    def __init__(self, cls: Type[DataclassType], data, fields: Collection[str]):
        super().__init__(cls, [], data)
        self._fields = fields

    @property
    def message(self):
        if len(self._fields) == 1:
            field = next(iter(self._fields))
            return f'Missing field "{field}" in loaded {class_path(self._cls)}'
        else:
            return f'Missing fields {self._fields} in loaded {class_path(self._cls)}'


class ModelContainsAny(Exception):
    def __init__(self, cls: Type):
        super().__init__(
            f'${class_path(cls)} contains fields annotated as Any or missing type annotation. '
            f'Provide a type annotation or pass `allow_any=True` to the serializer. '
            f'This may also be an ambiguous `Generic` definitions like `x: list`, `x: List` '
            f'which are resolved as `List[Any]`. '
        )
