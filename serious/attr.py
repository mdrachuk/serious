from __future__ import annotations

from dataclasses import dataclass, fields
from typing import Type, Any, Iterator, get_type_hints

from serious.utils import DataClass

serious = 'serious'


@dataclass(frozen=True)
class Attr:
    of: Type[DataClass]
    name: str
    type: Type
    metadata: Any

    @property
    def contains_serious_metadata(self):
        return self.metadata is not None and serious in self.metadata

    @property
    def serious_metadata(self):
        return self.metadata[serious]

    @staticmethod
    def list(cls: Type[DataClass]) -> Iterator[Attr]:
        types = get_type_hints(cls)
        return (Attr(cls, f.name, types[f.name], f.metadata) for f in fields(cls))
