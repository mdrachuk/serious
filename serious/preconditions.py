"""Checks performed in other places, throwing errors when unsatisfied.

Think [Guava Precondition](https://github.com/google/guava/wiki/PreconditionsExplained).
"""
from dataclasses import is_dataclass
from typing import TypeVar, Type, Optional

T = TypeVar('T')


def _check_is_instance(value: T, type_: Type[T], message: str = None) -> T:
    """Checks the value type, raising a TypeError.
    :return: provided value
    """
    message = message or f'Got "{value}" when expecting a "{type_}" instance.'
    if not isinstance(value, type_):
        raise TypeError(message)
    return value


def _check_is_dataclass(type_: Type[T], message: str = 'Not a dataclass') -> Type[T]:
    """Checks if the type is a dataclass, raising a TypeError.
    :return: provided type"""
    if not is_dataclass(type_):
        raise TypeError(message)
    return type_


def _check_present(optional: Optional[T], message: str = 'Value must be present') -> T:
    if optional is None:
        raise ValueError(message)
    value: T = optional
    return value
