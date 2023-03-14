from dataclasses import dataclass
from dataclasses import dataclass
from typing import Union

from serious import JsonModel


@dataclass(frozen=True)
class DataWithUnion:
    something: Union[str, int]


class TestEnum:
    def setup(self):
        self.model = JsonModel(DataWithUnion)

    def test_load(self):
        union = DataWithUnion('test')
        union_json = '{"something": {"__type__": "str", "__value__": "test"}}'
        assert self.model.load(union_json) == union

        int_union = DataWithUnion(69)
        int_union_json = '{"something": {"__type__": "int", "__value__": 69}}'
        assert self.model.load(int_union_json) == int_union

    def test_dump(self):
        union = DataWithUnion('test')
        union_json = '{"something": {"__type__": "str", "__value__": "test"}}'
        assert self.model.dump(union) == union_json

        int_union = DataWithUnion(-1)
        int_union_json = '{"something": {"__type__": "int", "__value__": -1}}'
        assert self.model.dump(int_union) == int_union_json
