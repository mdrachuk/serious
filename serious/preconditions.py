"""Checks performed in other places, throwing errors when unsatisfied.

Think [Guava Precondition](https://github.com/google/guava/wiki/PreconditionsExplained).
"""
from typing import TypeVar, Type

T = TypeVar('T')


def _check_is_instance(value: T, type_: Type[T], message: str = None) -> T:
    message = message or f'Got "{value}" when expecting a "{type_}" instance.'
    assert isinstance(value, type_), message
    return value
