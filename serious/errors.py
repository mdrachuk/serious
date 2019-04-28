from typing import Type, Mapping, Collection

from serious.utils import DataClass, _class_path


class SerializationError(Exception):
    def __init__(self, cls: Type[DataClass], serializer_stack: Collection[str]):
        super().__init__()
        self._cls = cls
        self._path = self.__parse_stack(serializer_stack)

    @staticmethod
    def __parse_stack(serializer_stack: Collection[str]) -> str:
        if len(serializer_stack) == 0:
            return ''
        return ''.join(serializer_stack)[1:]

    @property
    def message(self):
        return f'Error during serialization of "{self._cls}"'

    def __str__(self):
        exc_type = super().__str__()
        return f'{exc_type}: {self.message}'


class LoadError(SerializationError):
    def __init__(self, cls: DataClass, serializer_stack: Collection[str], data: Mapping):
        super().__init__(cls, serializer_stack)
        self._data = data

    @property
    def message(self):
        return f'Failed to load "{self._path}" of {_class_path(self._cls)} from {self._data}: {self.__cause__}'


class DumpError(SerializationError):
    def __init__(self, obj: DataClass, serializer_stack: Collection[str]):
        super().__init__(type(obj), serializer_stack)
        self._object = obj

    @property
    def message(self):
        return f'Failed to dump "{self._path}" of {self._object}: {self.__cause__}'


class UnexpectedItem(Exception):
    def __init__(self, fields: Collection[str], cls: Type[DataClass]):
        if len(fields) == 1:
            field = next(iter(fields))
            message = f'Unexpected field "{field}" in loaded {_class_path(cls)}'
        else:
            message = f'Unexpected fields {fields} in loaded {_class_path(cls)}'
        super().__init__(message)


class MissingField(Exception):
    def __init__(self, fields: Collection[str], cls: Type[DataClass]):
        if len(fields) == 1:
            field = next(iter(fields))
            message = f'Missing field "{field}" in loaded {_class_path(cls)}'
        else:
            message = f'Missing fields {fields} in loaded {_class_path(cls)}'
        super().__init__(message)
