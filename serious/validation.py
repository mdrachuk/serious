from typing import TypeVar

T = TypeVar('T')


def validate(obj: T) -> T:
    if hasattr(obj, '__validate__'):
        result = obj.__validate__()  # type: ignore # method presence checked above
        assert result is None, 'Validators should not return anything. Raise ValidationError instead'
    return obj
