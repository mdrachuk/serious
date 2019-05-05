from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import Any, Dict, List

from serious.dict import dict_schema


@dataclass(frozen=True)
class User:
    name: Any
    height: Any
    registered: Any
    meta: Dict[str, List]


schema = dict_schema(User)
now = datetime.now()
height = Decimal('1.76')

keith = User('Keith', height, now, {})
keith_dict = dict(name='Keith', height=height, registered=now, meta={})

meta = {'app1': [{'age': 13}], 'contact': [keith]}
albert_meta = User('Albert', Decimal('2'), now, meta)
albert_dict = dict(name='Albert', height=Decimal('2'), registered=now, meta=meta)


class TestAny:
    def test_load(self):
        actual = schema.load(keith_dict)
        assert actual == keith

    def test_dump(self):
        actual = schema.dump(keith)
        assert actual == keith_dict

    def test_nested_implicit_any_load(self):
        actual = schema.load(albert_dict)
        assert actual.meta == meta

    def test_nested_implicit_any_dump(self):
        actual = schema.dump(albert_meta)
        assert actual['meta'] == meta
