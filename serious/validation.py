from typing import TypeVar, Any

from serious.errors import ValidationError

A = TypeVar('A')


def validate(rule: bool, message='Failed validation') -> None:
    """Validate the """
    if not rule:
        raise ValidationError(message)


def validate_object(obj: Any) -> None:
    if hasattr(obj, '__validate__'):
        obj.__validate__()
