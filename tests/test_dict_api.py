from uuid import UUID

import pytest

from serious.dict import schema, Loading
from serious.errors import LoadError
from tests.entities import (DataClassWithDataClass, DataClassWithOptional,
                            DataClassWithOptionalNested, DataClassWithUuid)

allow_missing = Loading(allow_missing=True)
allow_unexpected = Loading(allow_unexpected=True)


class TestTypes:
    uuid_s = 'd1d61dd7-c036-47d3-a6ed-91cc2e885fc8'
    uuid = UUID(uuid_s)
    dc_uuid_json = {"id": uuid_s}
    schema = schema(DataClassWithUuid)

    def test_uuid_encode(self):
        actual = self.schema.dump(DataClassWithUuid(self.uuid))
        assert actual == self.dc_uuid_json

    def test_uuid_decode(self):
        actual = self.schema.load(self.dc_uuid_json)
        assert actual == DataClassWithUuid(self.uuid)


class TestAllowMissing:
    def test_allow_missing(self):
        actual = schema(DataClassWithOptional, load=allow_missing).load({})
        assert actual == DataClassWithOptional(None)

    def test_allow_missing_is_recursive(self):
        actual = schema(DataClassWithOptionalNested, load=allow_missing).load({"x": {}})
        expected = DataClassWithOptionalNested(DataClassWithOptional(None))
        assert actual == expected

    def test_allow_missing_terminates_at_first_missing(self):
        actual = schema(DataClassWithOptionalNested, load=allow_missing).load({"x": None})
        assert actual == DataClassWithOptionalNested(None)

    def test_error_when_missing_required(self):
        with pytest.raises(LoadError) as exc_info:
            schema(DataClassWithDataClass).load({"dc_with_list": {}})
        assert 'dc_with_list' in exc_info.value.message
        assert 'xs' in exc_info.value.message


class TestAllowUnexpected:
    def test_allow_unexpected(self):
        actual = schema(DataClassWithOptional, load=allow_unexpected).load({"x": None, "y": True})
        assert actual == DataClassWithOptional(None)

    def test_allow_unexpected_is_recursive(self):
        actual = schema(DataClassWithOptionalNested, load=allow_unexpected).load({"x": {"x": None, "y": "test"}})
        expected = DataClassWithOptionalNested(DataClassWithOptional(None))
        assert actual == expected

    def test_error_when_unexpected(self):
        with pytest.raises(LoadError) as exc_info:
            schema(DataClassWithOptional, load=Loading(allow_unexpected=False)).load({"x": 1, "y": 1})
        assert '"y"' in exc_info.value.message

    def test_error_when_unexpected_by_default(self):
        with pytest.raises(LoadError) as exc_info:
            schema(DataClassWithOptional).load({"x": 1, "y": 1})
        assert '"y"' in exc_info.value.message