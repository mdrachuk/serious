from typing import TypeVar, Any

A = TypeVar('A')


def validate(obj: Any) -> None:
    if hasattr(obj, '__validate__'):
        result = obj.__validate__()
        assert result is None, 'Validators should not return anything. Raise ValidationError instead'
