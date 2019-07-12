from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import Any, Dict, List

from serious.dict import DictSchema


@dataclass(frozen=True)
class User:
    name: Any
    height: Any
    registered: Any
    meta: Dict[str, List]


class TestAny:

    def setup_class(self):
        self.schema = DictSchema(User)
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
