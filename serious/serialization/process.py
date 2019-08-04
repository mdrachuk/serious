from __future__ import annotations

from abc import ABC, abstractmethod
from contextlib import contextmanager
from typing import List, Any, NamedTuple, TypeVar

from serious.serialization.serializer import Serializer
from serious.types import FrozenList
from serious.validation import validate

M = TypeVar('M')  # Python model value
S = TypeVar('S')  # Serialized value


class Serialization(ABC):

    def __init__(self):
        self._steps: List[SerializationStep] = list()

    @contextmanager
    def _entering(self, step: str, serializer: Serializer):
        self._steps.append(SerializationStep(step, serializer))
        yield
        self._steps.pop()

    @property
    def stack(self) -> FrozenList[SerializationStep]:
        return FrozenList(self._steps)

    @abstractmethod
    def run(self, step: str, serializer: Serializer, value: Any) -> Any:
        raise NotImplementedError


class Loading(Serialization):
    def run(self, step: str, serializer: Serializer[M, S], value: S) -> M:
        with self._entering(step, serializer):
            result = serializer.load(value, self)
            return validate(result)


class Dumping(Serialization):
    def run(self, step: str, serializer: Serializer[M, S], o: M) -> S:
        with self._entering(step, serializer):
            return serializer.dump(o, self)


class SerializationStep(NamedTuple):
    name: str
    serializer: Serializer
