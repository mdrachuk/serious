"""Checks performed in other places, throwing errors when unsatisfied.

Think [Guava Precondition](https://github.com/google/guava/wiki/PreconditionsExplained).
"""
from dataclasses import is_dataclass
from typing import TypeVar, Type

T = TypeVar('T')


def _check_is_instance(value: T, type_: Type[T]) -> T:
    """Checks the value type, raising a TypeError.
    :return: provided value
    """
    if not isinstance(value, type_):
        raise TypeError(f'Got "{value}" when expecting a "{type_}" instance.')
    return value


def _check_is_dataclass(type_: Type[T]) -> Type[T]:
    """Checks if the type is a dataclass, raising a TypeError.
    :return: provided type"""
    if not is_dataclass(type_):
        raise TypeError('Serious can only operate on dataclasses.')
    return type_
