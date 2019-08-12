from typing import TypeVar

T = TypeVar('T')


def validate(obj: T) -> T:
    """Executes objects own validation.

    Serious defines this validation as an instance `__validate__` method raising `ValidationError`.
    It also does not return nothing or returns None.

    Example:

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
