"""
Serious has a simple understanding of what validation should be: a `__validate__` instance method raising ValidationError.

First of all, this puts all of validation together instead spreading it all over the place simplifying understanding.

Secondly, explicit `raise ValidationError` hits can be seen in test coverage which reduces possibility of missing them
in tests.

Serious runs objects `__validate__` method if it’s present during object load by default.
This can be overridden by passing `validate_on_load` and `validate_on_dump` to model.


You can run validation yourself by calling `serious.validation.validate(obj)` whenever you need.
"""
__all__ = ['validate']

from typing import TypeVar

T = TypeVar('T')


def validate(obj: T) -> T:
    """Executes objects own validation.

    Serious defines this validation as an instance `__validate__` method raising `ValidationError`.
    It also does not return nothing or returns None.

        :Example:

        @dataclass
        class Note:
            title: str
            content: str

            def __validate__(self):
                if not len(self.content):
                    raise ValidationError('Note cannot be empty')

        valid = Note('', 'A test!')
        validate(valid)  # nothing happens

        invalid = Note('', '')
        validate(invalid)  # raises ValidationError(...)
    """
    if hasattr(obj, '__validate__'):
        result = obj.__validate__()  # type: ignore # method presence checked above
        assert result is None, 'Validators should not return anything. Raise ValidationError instead'
    return obj
