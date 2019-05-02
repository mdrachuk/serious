from uuid import UUID

import pytest

from serious.dict import dict_schema
from serious.errors import LoadError
from tests.entities import (DataClassWithDataClass, DataClassWithOptional,
                            DataClassWithOptionalNested, DataClassWithUuid)


class TestDefaults:
    def test_dump(self):
        pass

    def test_load(self):
        pass

    def test_dump_many(self):
        pass

    def test_load_many(self):
        pass


class TestTypes:
    uuid_s = 'd1d61dd7-c036-47d3-a6ed-91cc2e885fc8'
    uuid = UUID(uuid_s)
    dc_uuid_json = {"id": uuid_s}
    schema = dict_schema(DataClassWithUuid)

    def test_uuid_encode(self):
        actual = self.schema.dump(DataClassWithUuid(self.uuid))
        assert actual == self.dc_uuid_json

    def test_uuid_decode(self):
        actual = self.schema.load(self.dc_uuid_json)
        assert actual == DataClassWithUuid(self.uuid)


class TestAllowMissing:
    def test_allow_missing(self):
        actual = dict_schema(DataClassWithOptional, allow_missing=True).load({})
        assert actual == DataClassWithOptional(None)

    def test_allow_missing_is_recursive(self):
        actual = dict_schema(DataClassWithOptionalNested, allow_missing=True).load({"x": {}})
        expected = DataClassWithOptionalNested(DataClassWithOptional(None))
        assert actual == expected

    def test_allow_missing_terminates_at_first_missing(self):
        actual = dict_schema(DataClassWithOptionalNested, allow_missing=True).load({"x": None})
        assert actual == DataClassWithOptionalNested(None)

    def test_error_when_missing_required(self):
        with pytest.raises(LoadError) as exc_info:
            dict_schema(DataClassWithDataClass).load({"dc_with_list": {}})
        assert 'dc_with_list' in exc_info.value.message
        assert 'xs' in exc_info.value.message


class TestAllowUnexpected:
    def test_allow_unexpected(self):
        actual = dict_schema(DataClassWithOptional, allow_unexpected=True).load({"x": None, "y": True})
        assert actual == DataClassWithOptional(None)

    def test_allow_unexpected_is_recursive(self):
        actual = dict_schema(DataClassWithOptionalNested, allow_unexpected=True).load({"x": {"x": None, "y": "test"}})
        expected = DataClassWithOptionalNested(DataClassWithOptional(None))
        assert actual == expected

    def test_error_when_unexpected(self):
        with pytest.raises(LoadError) as exc_info:
            dict_schema(DataClassWithOptional, allow_unexpected=False).load({"x": 1, "y": 1})
        assert '"y"' in exc_info.value.message

    def test_error_when_unexpected_by_default(self):
        with pytest.raises(LoadError) as exc_info:
            dict_schema(DataClassWithOptional).load({"x": 1, "y": 1})
        assert '"y"' in exc_info.value.message
