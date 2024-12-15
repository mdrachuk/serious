"""Loading/dumping context holding the current execution stack, calling serializers and validators."""
from __future__ import annotations

__all__ = ["SerializationContext"]

from abc import ABC
from collections import deque
from typing import Any, TypeVar, Deque, Iterable

from serious.validation import validate

M = TypeVar("M")  # Python model value
S = TypeVar("S")  # Serialized value

SerializationStep = tuple[str, Any]


class SerializationContext(ABC):
    """An abstract base class for the serialization context.

    Serialization context is created when executing `SeriousModel` load or dump and is passed inside
    all nested serializers.

    All of serializers are called via context to include them in stack and to perform
    all the necessary validation and processing
    """

    _stack: Deque[SerializationStep]
    validating: bool

    def __init__(self, steps: Iterable[SerializationStep], validating: bool):
        self._stack = deque(steps)
        self.validating = validating

    @property
    def _last_validated_value(self):
        return self._stack[-1][1]

    @property
    def path(self):
        return "".join([s[0] for s in self._stack])

    @property
    def stack(self) -> list[SerializationStep]:
        """The stack is included in errors, mentioning the fields, array indexes, dictionary keys, etc."""
        return list(self._stack)

    def __repr__(self):
        return f"<Context: {self.path}>"

    def validate(self, o):
        self._stack.append((f".__validate__()", o))
        validate(o)
        self._stack.pop()

    def _repr_last_validated_value(self):
        value_repr = repr(self._last_validated_value)
        if len(value_repr) > 50:
            return f"{value_repr[:50]}<...+{len(value_repr) - 50}>"
        return value_repr

    def failed_validation_at(self):
        value = self._repr_last_validated_value()
        return f'Failed validation of {value} at "{self.path}"'

    def enter(self, step: str, value: Any):
        self._stack.append((step, value))

    def exit(self):
        self._stack.pop()
