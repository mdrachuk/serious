from typing import Mapping, Any, Union, List, Type

DataclassType = Any
Primitive = Union[Mapping, List, str, int, float, bool, None]


def _class_path(cls: Type) -> str:
    return f'{cls.__module__}.{cls.__qualname__}'


def _is_optional(cls: Type) -> bool:
    return hasattr(cls, '__origin__') \
           and cls.__origin__ == Union \
           and len(cls.__args__) == 2 \
           and cls.__args__[1] == type(None)
