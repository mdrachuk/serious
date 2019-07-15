from typing import Mapping, Any, Union, List, Type

DataclassType = Any
Primitive = Union[Mapping, List, str, int, float, bool, None]


def class_path(cls: Type) -> str:
    """Returns a fully qualified type name."""
    return f'{cls.__module__}.{cls.__qualname__}'
