import json

from serious.json import json_schema
from tests.entities import DataClassWithDataClass, DataClassWithList, DataClassX, DataClassXs

dcwdc = json_schema(DataClassWithDataClass)
dcxs = json_schema(DataClassXs)


class TestEncoder:
    def test_nested_dataclass(self):
        actual = dcwdc.dump(DataClassWithDataClass(DataClassWithList([1])))
        expected = json.dumps({"dc_with_list": {"xs": [1]}})
        assert actual == expected

    def test_nested_list_of_dataclasses(self):
        actual = dcxs.dump(DataClassXs([DataClassX(0), DataClassX(1)]))
        expected = json.dumps({"xs": [{"x": 0}, {"x": 1}]})
        assert actual == expected


class TestDecoder:
    def test_nested_dataclass(self):
        actual = dcwdc.load(json.dumps({"dc_with_list": {"xs": [1]}}))
        expected = DataClassWithDataClass(DataClassWithList([1]))
        assert actual == expected

    def test_nested_list_of_dataclasses(self):
        actual = dcxs.load(json.dumps({"xs": [{"x": 0}, {"x": 1}]}))
        expected = DataClassXs([DataClassX(0), DataClassX(1)])
        assert actual == expected
