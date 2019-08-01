import json

from serious import JsonModel
from tests.entities import DataclassWithDataclass, DataclassWithList, DataclassX, DataclassXs


class TestDecoder:
    def setup_class(self):
        self.dcwdc = JsonModel(DataclassWithDataclass)
        self.dcxs = JsonModel(DataclassXs)

    def test_nested_dataclass(self):
        actual = self.dcwdc.load(json.dumps({"dc_with_list": {"xs": [1]}}))
        expected = DataclassWithDataclass(DataclassWithList([1]))
        assert actual == expected

    def test_nested_list_of_dataclasses(self):
        actual = self.dcxs.load(json.dumps({"xs": [{"x": 0}, {"x": 1}]}))
        expected = DataclassXs([DataclassX(0), DataclassX(1)])
        assert actual == expected


class TestEncoder:
    def setup_class(self):
        self.dcwdc = JsonModel(DataclassWithDataclass)
        self.dcxs = JsonModel(DataclassXs)

    def test_nested_dataclass(self):
        actual = self.dcwdc.dump(DataclassWithDataclass(DataclassWithList([1])))
        expected = json.dumps({"dc_with_list": {"xs": [1]}})
        assert actual == expected

    def test_nested_list_of_dataclasses(self):
        actual = self.dcxs.dump(DataclassXs([DataclassX(0), DataclassX(1)]))
        expected = json.dumps({"xs": [{"x": 0}, {"x": 1}]})
        assert actual == expected
