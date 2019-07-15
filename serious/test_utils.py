from typing import Union, Any

from serious.dict import DictSchema
from serious.json import JsonSchema

Dataclass = Any  # a dataclass instance


def assert_symmetric(serializer: Union[JsonSchema, DictSchema], value: Dataclass):
    """Asserts that dumping an instance of dataclass via schema and loading it will result in an equal object."""
    assert serializer.load(serializer.dump(value)) == value, f'load/dump are not symmetric in {serializer}.'
