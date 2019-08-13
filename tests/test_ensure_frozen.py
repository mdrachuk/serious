from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, time
from decimal import Decimal
from enum import Enum
from typing import List, Generic, TypeVar, Dict, Tuple, Set, Any, FrozenSet
from uuid import UUID

import pytest

from serious import FrozenList, JsonModel, DictModel, Email, Timestamp, FrozenDict, TypeDescriptor
from serious.errors import MutableTypesInModel, ModelContainsAny
from serious.serialization import FieldSerializer, field_serializers
from tests.utils import with_


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


@dataclass(frozen=True)
class FrozenEvent(Generic[T]):
    event: T


class MutNode:
    nodes: List[MutNode]

    def __init__(self, nodes: List[MutNode]):
        self.nodes = nodes


class FrozenNode:
    nodes: FrozenList[FrozenNode]

    def __init__(self, nodes: List[FrozenNode]):
        super().__setattr__('nodes', nodes)

    def __setattr__(self, name, value):
        raise AttributeError('Cannot change a frozen object.')


models = [JsonModel, DictModel]


@dataclass
class MutableDataclass:
    pass


@dataclass(frozen=True)
class ImmutableDataclass:
    pass


immutable = [str, int, float, bool,
             Tuple[str], Tuple[str, Ellipsis], FrozenList[str], FrozenSet[str],
             Decimal, UUID,
             datetime, date, time, Email, Timestamp,
             ImmutableDataclass]
mutable = [List[str], Dict[str, str], Set[str], Enum, MutableDataclass, MutNode]


@with_(models)
def test_ensure_default_non_frozen(new_model):
    model = new_model(BlogPost)
    assert model


@with_(models)
def test_ensure_frozen_false(new_model):
    model = new_model(BlogPost, ensure_frozen=False)
    assert model


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
            new_model(FrozenEvent[Dict[str, str]], ensure_frozen=True)

    @with_(models)
    def test_raises_model_error_on_generic_parameter(self, new_model):
        with pytest.raises(MutableTypesInModel):
            new_model(FrozenEvent[FrozenList[MutNode]], ensure_frozen=True)

    @with_(models)
    def test_passes_valid_model(self, new_model):
        model = new_model(User, ensure_frozen=True)
        assert model

    @with_(models, immutable)
    def test_immutable_types(self, new_model, cls):
        assert new_model(FrozenEvent[cls], ensure_frozen=True)

    @with_(models, mutable)
    def test_mutable_types(self, new_model, cls):
        with pytest.raises(MutableTypesInModel):
            assert new_model(FrozenEvent[cls], ensure_frozen=True)

    @with_(models, [Any, list, FrozenDict])
    def test_fails_any(self, new_model, cls):
        with pytest.raises(ModelContainsAny) as e:
            assert new_model(FrozenEvent[cls], ensure_frozen=True)
        assert 'ensure_frozen' in str(e)

    @with_(models, [str, FrozenNode, FrozenList[FrozenNode]])
    def test_custom_immutable_object(self, new_model, cls):
        assert new_model(FrozenEvent[cls], field_serializers([FrozenNodeSerializer]), ensure_frozen=[FrozenNode])


class FrozenNodeSerializer(FieldSerializer[FrozenNode, list]):
    @classmethod
    def fits(cls, desc: TypeDescriptor) -> bool:
        return desc.cls is FrozenNode

    def load(self, value, ctx):
        return FrozenNode(value)

    def dump(self, value, ctx):
        return value.nodes
