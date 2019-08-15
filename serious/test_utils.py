"""
Test utilities for use with pytest.

Right now contains single check -- `assert_symmetric`.
With it’s possible to check that a dataclass stays the same after dumping and loading the dumped instance.
"""

__all__ = ['assert_symmetric']

from typing import overload

from .dict import DictModel
from .json import JsonModel
from .utils import Dataclass


@overload
def assert_symmetric(serializer: DictModel, value: Dataclass):
    pass


@overload
def assert_symmetric(serializer: JsonModel, value: Dataclass):
    pass


def assert_symmetric(serializer, value):
    """Asserts that dumping an instance of dataclass via model and loading it will result in an equal object."""
    assert serializer.load(serializer.dump(value)) == value, f'load/dump are not symmetric in {serializer}.'
