"""Minor utilities used throughout the project."""

__all__ = ['class_path', 'Dataclass']

from typing import Type, Any

Dataclass = Any  # a dataclass instance


def class_path(cls: Type) -> str:
    """Returns a fully qualified type name."""
    return f'{cls.__module__}.{cls.__qualname__}'
