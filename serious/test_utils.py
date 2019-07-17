from typing import Any, overload

from serious.dict import DictSchema
from serious.json import JsonSchema

Dataclass = Any  # a dataclass instance


@overload
def assert_symmetric(serializer: DictSchema, value: Dataclass):
    pass


@overload
def assert_symmetric(serializer: JsonSchema, value: Dataclass):
    pass


def assert_symmetric(serializer, value):
    """Asserts that dumping an instance of dataclass via schema and loading it will result in an equal object."""
    assert serializer.load(serializer.dump(value)) == value, f'load/dump are not symmetric in {serializer}.'
