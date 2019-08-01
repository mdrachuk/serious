from typing import Any, overload

from .dict import DictModel
from .json import JsonModel

Dataclass = Any  # a dataclass instance


@overload
def assert_symmetric(serializer: DictModel, value: Dataclass):
    pass


@overload
def assert_symmetric(serializer: JsonModel, value: Dataclass):
    pass


def assert_symmetric(serializer, value):
    """Asserts that dumping an instance of dataclass via model and loading it will result in an equal object."""
    assert serializer.load(serializer.dump(value)) == value, f'load/dump are not symmetric in {serializer}.'
