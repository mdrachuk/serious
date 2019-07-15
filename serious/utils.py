from typing import Mapping, Any, Union, List, Type

DataclassType = Any
Primitive = Union[Mapping, List, str, int, float, bool, None]


def class_path(cls: Type) -> str:
    """Returns a fully qualified type name."""
    return f'{cls.__module__}.{cls.__qualname__}'


def is_optional(cls: Type) -> bool:
    """Returns True if the provided type is Optional."""
    return hasattr(cls, '__origin__') \
           and cls.__origin__ == Union \
           and len(cls.__args__) == 2 \
           and cls.__args__[1] == type(None)
