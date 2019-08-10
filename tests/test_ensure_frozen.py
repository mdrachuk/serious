from __future__ import annotations

import inspect
from dataclasses import dataclass
from datetime import date, datetime, time
from decimal import Decimal
from enum import Enum
from itertools import product
from typing import List, Sequence, Generic, TypeVar, Dict, Tuple, Set
from uuid import UUID

import pytest

from serious import FrozenList, JsonModel, DictModel, Email, Timestamp


@dataclass(frozen=True)
class User:
    id: int
    name: str
    invitees: FrozenList[User]


@dataclass(frozen=True)
class BlogPost:
    title: str
    content: str
    tags: List[str]


@dataclass
class Message:
    sender: User
    receiver: User
    content: str


T = TypeVar('T')


@dataclass
class InternalEvent(Generic[T]):
    event: T


class Node:
    nodes: List[Node]

    def __init__(self, nodes: List[Node]):
        self.nodes = nodes


models = [JsonModel, DictModel]


def with_(*collections: Sequence[Sequence], cartesian_product=True):
    def _wrapped(f):
        signature = inspect.signature(f)
        func_params = list(signature.parameters)
        if len(func_params) and func_params[0] == 'self':
            func_params.pop(0)
        pytest_keys = ','.join(func_params)
        if cartesian_product:
            pytest_values = list(product(*collections))
        else:
            if len(set(map(len, collections))) != 1:
                raise Exception('Parameters must be of equal length')
            pytest_values = list(zip(*collections))
        return pytest.mark.parametrize(pytest_keys, pytest_values)(f)

    return _wrapped


@with_(models)
def test_ensure_default_non_frozen(new_model):
    model = new_model(BlogPost)
    assert model
    assert model.ensure_frozen is False


@with_(models)
def test_ensure_frozen_false(new_model):
    model = new_model(BlogPost, ensure_frozen=False)
    assert model
    assert model.ensure_frozen is False


@dataclass
class MutableDataclass:
    pass


@dataclass(frozen=True)
class ImmutableDataclass:
    pass


immutable = [
    str, int, float, bool, Tuple[str], Decimal, UUID, datetime, date, time, Email, Timestamp, ImmutableDataclass
]
mutable = [List[str], Dict[str, str], Set[str], Enum, MutableDataclass]


class TestEnsureFrozenTrue:

    @with_(models)
    def test_raises_model_error_on_field(self, new_model):
        with pytest.raises(MutableTypesInModel):
            new_model(BlogPost, ensure_frozen=True)

    @with_(models)
    def test_raises_model_error_on_dataclass(self, new_model):
        with pytest.raises(MutableTypesInModel):
            new_model(Message, ensure_frozen=True)

    @with_(models)
    def test_raises_model_error_on_generic_parameter(self, new_model):
        with pytest.raises(MutableTypesInModel):
            new_model(InternalEvent[Dict[str, str]], ensure_frozen=True)

    @with_(models)
    def test_raises_model_error_on_generic_parameter(self, new_model):
        with pytest.raises(MutableTypesInModel):
            new_model(InternalEvent[FrozenList[Node]], ensure_frozen=True)

    @with_(models)
    def test_passes_valid_model(self, new_model):
        model = new_model(User, ensure_frozen=True)
        assert model
        assert model.ensure_frozen

    @with_(models, immutable)
    def test_immutable_types(self, new_model, cls):
        assert new_model(InternalEvent[cls], ensure_frozen=True)

    @with_(models, mutable)
    def test_mutable_types(self, new_model, cls):
        with pytest.raises(MutableTypesInModel):
            assert new_model(InternalEvent[cls], ensure_frozen=True)
