"""Loading/dumping context holding the current execution stack, calling serializers and validators."""
from __future__ import annotations

__all__ = ['Context', 'Loading', 'Dumping']

from abc import ABC, abstractmethod
from collections import deque
from typing import Any, TypeVar, Deque

from serious.serialization.serializer import Serializer
from serious.types import FrozenList
from serious.validation import validate

M = TypeVar('M')  # Python model value
S = TypeVar('S')  # Serialized value

SerializationStep = str


class Context(ABC):
    """An abstract base class for the serialization context.

    Serialization context is created when executing `SeriousModel` load or dump and is passed inside
    all nested serializers.

    All of serializers are called via context to include them in stack and to perform
    all the necessary validation and processing
    """
    _steps: Deque[SerializationStep]

    @property
    def stack(self) -> FrozenList[SerializationStep]:
        """The stack is included in errors, mentioning the fields, array indexes, dictionary keys, etc."""
        return FrozenList(self._steps)

    def __repr__(self):
        return f"<Context: {'.'.join(self._steps)}>"

    @abstractmethod
    def run(self, step: str, serializer: Serializer, value: Any) -> Any:
        """Execute serializer in context.

        Implementations:
        - includes the current step in the stack,
        - executes current steps serializer,
        - performs any required processing of values.

        This abstraction is needed for a straightforward custom serializer implementation.
        Extracting validation (or any other value processing) from serializers to `Context#run(...)`
        has left field serializers with a plain structure of a constructor, load, dump, and fits methods.
        """
        raise NotImplementedError


class Loading(Context):
    """Context used during **load** operations."""

    def __init__(self, *, validating: bool):
        super().__init__()
        self._steps = deque()
        self.validating = validating

    def run(self, step: str, serializer: Serializer[M, S], value: S) -> M:
        self._steps.append(step)
        result = serializer.load(value, self)
        if self.validating:
            validate(result)
        self._steps.pop()
        return result


class Dumping(Context):
    """Context used during **dump** operations."""

    def __init__(self, *, validating: bool):
        super().__init__()
        self._steps = deque()
        self.validating = validating

    def run(self, step: str, serializer: Serializer[M, S], o: M) -> S:
        self._steps.append(step)
        if self.validating:
            validate(o)
        result = serializer.dump(o, self)
        self._steps.pop()
        return result
