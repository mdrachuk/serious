from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import Any, Dict, List

import pytest

from serious import DictModel, JsonModel
from serious.errors import ModelContainsAny


@dataclass(frozen=True)
class User:
    name: Any
    height: Any
    registered: Any
    meta: Dict[str, List]


class TestAny:

    def setup_class(self):
        self.model = DictModel(User, allow_any=True)
        now = datetime.now()
        height = Decimal('1.76')

        self.keith = User('Keith', height, now, {})
        self.keith_dict = dict(name='Keith', height=height, registered=now, meta={})

        self.meta = {'app1': [{'age': 13}], 'contact': [self.keith]}
        self.albert_meta = User('Albert', Decimal('2'), now, self.meta)
        self.albert_dict = dict(name='Albert', height=Decimal('2'), registered=now, meta=self.meta)

    def test_load(self):
        actual = self.model.load(self.keith_dict)
        assert actual == self.keith

    def test_dump(self):
        actual = self.model.dump(self.keith)
        assert actual == self.keith_dict

    def test_nested_implicit_any_load(self):
        actual = self.model.load(self.albert_dict)
        assert actual.meta == self.meta

    def test_nested_implicit_any_dump(self):
        actual = self.model.dump(self.albert_meta)
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
        assert DictModel(Thing)
        with pytest.raises(ModelContainsAny):
            DictModel(Something)

    def test_explicit_with_any(self):
        assert DictModel(Something, allow_any=True)
        with pytest.raises(ModelContainsAny):
            assert DictModel(Something, allow_any=False)

    def test_explicit_without_any(self):
        assert DictModel(Thing, allow_any=True)
        assert DictModel(Thing, allow_any=False)

    def test_explicit_with_collection_of_any(self):
        assert DictModel(Closet, allow_any=True)
        with pytest.raises(ModelContainsAny):
            assert DictModel(Closet, allow_any=False)


class TestAllowAnyInDict:

    def test_default(self):
        assert JsonModel(Thing)
        with pytest.raises(ModelContainsAny):
            JsonModel(Something)

    def test_explicit_with_any(self):
        assert JsonModel(Something, allow_any=True)
        with pytest.raises(ModelContainsAny):
            assert JsonModel(Something, allow_any=False)

    def test_explicit_without_any(self):
        assert JsonModel(Thing, allow_any=True)
        assert JsonModel(Thing, allow_any=False)
