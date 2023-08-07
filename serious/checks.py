"""Checks performed in other places, throwing errors when unsatisfied. """
from typing import TypeVar, Type, Optional

T = TypeVar('T')


def check_is_instance(value: T, type_: Type[T], message: Optional[str] = None) -> T:
    message = message or f'Got "{value}" when expecting a "{type_}" instance.'
    if not isinstance(value, type_):
        raise TypeError(message)
    return value
