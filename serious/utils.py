from typing import Any, Type

DataclassType = Any


def class_path(cls: Type) -> str:
    """Returns a fully qualified type name."""
    return f'{cls.__module__}.{cls.__qualname__}'
