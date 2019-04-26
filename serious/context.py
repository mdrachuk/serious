from __future__ import annotations

from contextlib import contextmanager
from typing import List, Tuple


class SerializationContext:
    def __init__(self, _root: SerializationContext = None):
        self._stack: List[str] = list()
        self._root: SerializationContext = _root or self

    @contextmanager
    def enter(self, name: str):
        self._stack.append(name)
        yield
        self._stack.pop()

    @property
    def is_root(self) -> bool:
        return self._root is self

    @property
    def root(self) -> SerializationContext:
        return self._root

    @property
    def stack(self) -> Tuple[str, ...]:
        return tuple(self._stack)
