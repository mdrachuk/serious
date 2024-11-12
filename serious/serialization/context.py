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
    validating: bool
    _last_validated_value: Any

    def __init__(self, steps: Deque[SerializationStep], validating: bool):
        self._steps = steps
        self.validating = validating
        self._last_validated_value = None

    @property
    def path(self):
        return ''.join(self._steps)

    @property
    def stack(self) -> FrozenList[SerializationStep]:
        """The stack is included in errors, mentioning the fields, array indexes, dictionary keys, etc."""
        return FrozenList(self._steps)

    def __repr__(self):
        return f"<Context: {self.path}>"

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

    def validate(self, o):
        self._steps.append(f".__validate__()")
        self._last_validated_value = o
        validate(o)
        self._steps.pop()

    def _repr_last_validated_value(self):
        value_repr = repr(self._last_validated_value)
        if len(value_repr) > 50:
            return f'{value_repr[:50]}<...+{len(value_repr) - 50}>'
        return value_repr

    def failed_validation_at(self):
        value = self._repr_last_validated_value()
        return f"Failed validation of {value} at \"{self.path}\""

class Loading(Context):
    """Context used during **load** operations."""

    def __init__(self, *, validating: bool, root: str = '__root__', steps: Deque[SerializationStep] | None = None):
        if steps is None:
            steps = deque()
            steps.append(root)
        super().__init__(steps, validating)

    def run(self, step: str, serializer: Serializer[M, S], value: S) -> M:
        self._steps.append(step)
        self._last_validated_value = value
        result = serializer.load(value, self)
        if self.validating:
            self.validate(result)
        self._steps.pop()
        return result



class Dumping(Context):
    """Context used during **dump** operations."""

    def __init__(self, *, validating: bool, root: str = '.', steps: Deque[SerializationStep] | None = None):
        if steps is None:
            steps = deque()
            steps.append(root)
        super().__init__(steps, validating)

    def run(self, step: str, serializer: Serializer[M, S], o: M) -> S:
        self._steps.append(step)
        if self.validating:
            self.validate(o)
        self._last_validated_value = o
        result = serializer.dump(o, self)
        self._steps.pop()
        return result

    def validation_proxy(self) -> Loading:
        return DumpingValidationProxy(self)


class DumpingValidationProxy(Loading):
    def __init__(self, ctx: Dumping):
        super().__init__(validating=False)
        self._ctx = ctx

    @property
    def _steps(self):
        return self._ctx._steps

    @_steps.setter
    def _steps(self, value):
        pass

    @property
    def _last_validated_value(self):
        return self._ctx._last_validated_value

    @_last_validated_value.setter
    def _last_validated_value(self, value):
        pass
