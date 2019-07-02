from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from serious.json import JsonSerializer


@dataclass(frozen=True)
class Tree:
    value: str
    left: Optional[Tree]
    right: Optional[Tree]


def family_tree_json():
    return """
{
    "value": "Boy",
    "left": {
        "value": "Ma",
        "left": {
            "value": "Maternal Grandma",
            "left": null,
            "right": null
        },
        "right": {
            "value": "Maternal Grandpa",
            "left": null,
            "right": null
        }
    },
    "right": {
        "value": "Pa",
        "left": {
            "value": "Paternal Grandma",
            "left": null,
            "right": null
        },
        "right": {
            "value": "Paternal Grandpa",
            "left": null,
            "right": null
        }
    }
}
""".strip()


def family_tree():
    return Tree(
        "Boy",
        Tree(
            "Ma",
            Tree("Maternal Grandma", None, None),
            Tree("Maternal Grandpa", None, None)
        ),
        Tree(
            "Pa",
            Tree("Paternal Grandma", None, None),
            Tree("Paternal Grandpa", None, None)
        ),
    )


class TestRecursive:

    def setup_class(self):
        self.o = family_tree()
        self.json = family_tree_json()

    def test_tree_decode(self):
        assert JsonSerializer(Tree).load(self.json) == self.o

    def test_tree_encode(self):
        assert JsonSerializer(Tree, indent=4).dump(self.o) == self.json
