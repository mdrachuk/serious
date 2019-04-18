import json

from serious import load, asjson
from tests.entities import DataClassWithDataClass, DataClassWithList, DataClassX, DataClassXs


class TestEncoder:
    def test_nested_dataclass(self):
        actual = asjson(DataClassWithDataClass(DataClassWithList([1])))
        expected = json.dumps({"dc_with_list": {"xs": [1]}})
        assert actual == expected

    def test_nested_list_of_dataclasses(self):
        actual = asjson(DataClassXs([DataClassX(0), DataClassX(1)]))
        expected = json.dumps({"xs": [{"x": 0}, {"x": 1}]})
        assert actual == expected


class TestDecoder:
    def test_nested_dataclass(self):
        actual = load(DataClassWithDataClass).from_(json.dumps({"dc_with_list": {"xs": [1]}}))
        expected = DataClassWithDataClass(DataClassWithList([1]))
        assert actual == expected

    def test_nested_list_of_dataclasses(self):
        actual = load(DataClassXs).from_(json.dumps({"xs": [{"x": 0}, {"x": 1}]}))
        expected = DataClassXs([DataClassX(0), DataClassX(1)])
        assert actual == expected
