from typing import Union, Any

from serious.dict import DictSchema
from serious.json import JsonSchema

Dataclass = Any  # a dataclass instance


def assert_symmetric(serializer: Union[JsonSchema, DictSchema], value: Dataclass):
    assert serializer.load(serializer.dump(value)) == value, f'load/dump are not symmetric in {serializer}.'
