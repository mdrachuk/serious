from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from serious.json import json_schema, Dumping


@dataclass(frozen=True)
class Tree:
    value: str
    left: Optional[Tree]
    right: Optional[Tree]


family_tree_json = """
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

family_tree = Tree(
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
    def test_tree_encode(self):
        assert json_schema(Tree, Dumping(indent=4)).dump(family_tree) == family_tree_json

    def test_tree_decode(self):
        assert json_schema(Tree).load(family_tree_json) == family_tree
