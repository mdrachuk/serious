from __future__ import annotations

from abc import abstractmethod, ABC
from contextlib import contextmanager
from typing import List

from serious.types import FrozenList, FrozenList


class SerializationStep(ABC):

    @abstractmethod
    def step_name(self) -> str:
        raise NotImplementedError


class SerializationContext:
    def __init__(self):
        self._steps: List[SerializationStep] = list()

    @contextmanager
    def enter(self, step: SerializationStep):
        self._steps.append(step)
        yield
        self._steps.pop()

    @property
    def stack(self) -> FrozenList[SerializationStep]:
        return FrozenList(self._steps)
