"""Checks performed in other places, throwing errors when unsatisfied."""

import collections
from typing import Any, Type

from serious.json.errors import UnexpectedJson


def check_that_loading_an_object(data: Any, cls: Type):
    """Checks data is a Mapping. If not raises an `serious.json.errors.UnexpectedJson` with a helpful error message."""

    if not isinstance(data, collections.abc.Mapping):
        if isinstance(data, collections.abc.Collection):
            raise UnexpectedJson(f'Expecting a single object in JSON, got a collection instead. '
                                 f'Use #load_all(cls) instead of #load(cls) '
                                 f'to decode an array of {cls} dataclasses.')
        raise UnexpectedJson(f'Expecting a single {cls} object encoded in JSON.')


def check_that_loading_a_list(data: Any, cls: Type):
    """Checks data is a Collection but not a Mapping.
    If not raises an `serious.json.errors.UnexpectedJson` with a helpful error message.
    """

    if not isinstance(data, collections.abc.Collection):
        raise UnexpectedJson(f'Expecting an array of {cls} objects encoded in JSON.')
    if isinstance(data, collections.abc.Mapping):
        raise UnexpectedJson(f'Expecting an array of objects encoded in JSON, got a mapping instead.'
                             f'Use #load(cls) instead of #load_all(cls) '
                             f'to decode a single {cls} dataclasses.')
