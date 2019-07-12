"""Checks performed in other places, throwing errors when unsatisfied.

Think [Guava Precondition](https://github.com/google/guava/wiki/PreconditionsExplained).
"""
from dataclasses import is_dataclass
from typing import TypeVar, Type, Optional

T = TypeVar('T')


def _check_is_instance(value: T, type_: Type[T], message: str = None) -> T:
    message = message or f'Got "{value}" when expecting a "{type_}" instance.'
    assert isinstance(value, type_), message
    return value


def _check_is_dataclass(type_: Type[T], message: str = 'Not a dataclass') -> Type[T]:
    assert is_dataclass(type_), message
    return type_


def _check_present(optional: Optional[T], message: str = 'Value must be present') -> T:
    assert optional is not None, message
    value: T = optional
    return value


def _check_exactly_one_present(*args, message: str = 'Exactly one parameter is expected to be non-None'):
    flag = False
    for arg in args:
        if arg is not None:
            _check_present(message)
            flag = True
    assert flag, message
