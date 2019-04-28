from __future__ import annotations

from contextlib import contextmanager
from typing import List, Tuple


class SerializationContext:
    def __init__(self):
        self._stack: List[str] = list()

    @contextmanager
    def enter(self, name: str):
        self._stack.append(name)
        yield
        self._stack.pop()

    @property
    def stack(self) -> Tuple[str, ...]:
        return tuple(self._stack)
