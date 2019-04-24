from typing import Type, List, Mapping, Collection

from serious.utils import DataClass, _class_path


class SerializationError(Exception):
    def __init__(self, cls: Type[DataClass], serializer_stack: List[str]):
        self._cls = cls
        self._path = self.__parse_stack(serializer_stack)
        super().__init__(self._message())

    @staticmethod
    def __parse_stack(serializer_stack: List[str]) -> str:
        if len(serializer_stack) == 0:
            return ''
        return ''.join(serializer_stack)[1:]

    def _message(self):
        return f'Error during serialization of "{self._cls}"'


class LoadError(SerializationError):
    def __init__(self, cls: DataClass, serializer_stack: List[str], data: Mapping):
        self._data = data
        super().__init__(cls, serializer_stack)

    def _message(self):
        return f'Failed to load "{self._path}" of {_class_path(self._cls)} from {self._data}'


class DumpError(SerializationError):
    def __init__(self, obj: DataClass, serializer_stack: List[str]):
        self._object = obj
        super().__init__(type(obj), serializer_stack)

    def _message(self):
        return f'Failed to dump "{self._path}" of {self._object}'


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
