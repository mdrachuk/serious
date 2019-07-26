from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import Any, Dict, List

import pytest

from serious import DictSchema, JsonSchema
from serious.errors import ModelContainsAny


@dataclass(frozen=True)
class User:
    name: Any
    height: Any
    registered: Any
    meta: Dict[str, List]


class TestAny:

    def setup_class(self):
        self.schema = DictSchema(User, allow_any=True)
        now = datetime.now()
        height = Decimal('1.76')

        self.keith = User('Keith', height, now, {})
        self.keith_dict = dict(name='Keith', height=height, registered=now, meta={})

        self.meta = {'app1': [{'age': 13}], 'contact': [self.keith]}
        self.albert_meta = User('Albert', Decimal('2'), now, self.meta)
        self.albert_dict = dict(name='Albert', height=Decimal('2'), registered=now, meta=self.meta)

    def test_load(self):
        actual = self.schema.load(self.keith_dict)
        assert actual == self.keith

    def test_dump(self):
        actual = self.schema.dump(self.keith)
        assert actual == self.keith_dict

    def test_nested_implicit_any_load(self):
        actual = self.schema.load(self.albert_dict)
        assert actual.meta == self.meta

    def test_nested_implicit_any_dump(self):
        actual = self.schema.dump(self.albert_meta)
        assert actual['meta'] == self.meta


@dataclass(frozen=True)
class Something:
    contents: Any


@dataclass(frozen=True)
class Closet:
    items: list


@dataclass(frozen=True)
class Thing:
    name: str


class TestAllowAnyInJson:

    def test_default(self):
        assert DictSchema(Thing)
        with pytest.raises(ModelContainsAny):
            DictSchema(Something)

    def test_explicit_with_any(self):
        assert DictSchema(Something, allow_any=True)
        with pytest.raises(ModelContainsAny):
            assert DictSchema(Something, allow_any=False)

    def test_explicit_without_any(self):
        assert DictSchema(Thing, allow_any=True)
        assert DictSchema(Thing, allow_any=False)

    def test_explicit_with_collection_of_any(self):
        assert DictSchema(Closet, allow_any=True)
        with pytest.raises(ModelContainsAny):
            assert DictSchema(Closet, allow_any=False)


class TestAllowAnyInDict:

    def test_default(self):
        assert JsonSchema(Thing)
        with pytest.raises(ModelContainsAny):
            JsonSchema(Something)

    def test_explicit_with_any(self):
        assert JsonSchema(Something, allow_any=True)
        with pytest.raises(ModelContainsAny):
            assert JsonSchema(Something, allow_any=False)

    def test_explicit_without_any(self):
        assert JsonSchema(Thing, allow_any=True)
        assert JsonSchema(Thing, allow_any=False)
