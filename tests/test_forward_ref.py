import json

from serious import JsonModel
from tests.entities import DataclassWithForwardRef
from tests.entities_str import DataclassWithForwardRefStr


class TestDecoder:
    def setup_class(self):
        self.dcwfr = JsonModel(DataclassWithForwardRef)
        self.dcwfrs = JsonModel(DataclassWithForwardRefStr)

    def test_forward_ref(self):
        actual = self.dcwfr.load(json.dumps({"child": {"child": None}}))
        expected = DataclassWithForwardRef(DataclassWithForwardRef(None))
        assert actual == expected

    def test_forward_ref_str(self):
        actual = self.dcwfrs.load(json.dumps({"child": {"child": None}}))
        expected = DataclassWithForwardRefStr(DataclassWithForwardRefStr(None))
        assert actual == expected


class TestEncoder:
    def setup_class(self):
        self.dcwfr = JsonModel(DataclassWithForwardRef)
        self.dcwfrs = JsonModel(DataclassWithForwardRefStr)

    def test_forward_ref(self):
        actual = self.dcwfr.dump(DataclassWithForwardRef(DataclassWithForwardRef(None)))
        expected = json.dumps({"child": {"child": None}})
        assert actual == expected

    def test_forward_ref_str(self):
        actual = self.dcwfrs.dump(DataclassWithForwardRefStr(DataclassWithForwardRefStr(None)))
        expected = json.dumps({"child": {"child": None}})
        assert actual == expected
