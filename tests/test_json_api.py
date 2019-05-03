from uuid import UUID

import pytest

from serious.errors import LoadError
from serious.json import json_schema
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

    def test_serializers(self):
        pass


class TestTypes:
    uuid_s = 'd1d61dd7-c036-47d3-a6ed-91cc2e885fc8'
    dc_uuid_json = f'{{"id": "{uuid_s}"}}'
    uuid_schema = json_schema(DataClassWithUuid)

    def test_uuid_encode(self):
        actual = self.uuid_schema.dump(DataClassWithUuid(UUID(self.uuid_s)))
        assert actual == self.dc_uuid_json

    def test_uuid_decode(self):
        actual = self.uuid_schema.load(self.dc_uuid_json)
        assert actual == DataClassWithUuid(UUID(self.uuid_s))


class TestAllowMissing:
    def test_allow_missing(self):
        actual = json_schema(DataClassWithOptional, allow_missing=True).load('{}')
        assert actual == DataClassWithOptional(None)

    def test_allow_unexpectetd_is_recursive(self):
        actual = json_schema(DataClassWithOptionalNested, allow_missing=True).load('{"x": {}}')
        expected = DataClassWithOptionalNested(DataClassWithOptional(None))
        assert actual == expected

    def test_allow_missing_terminates_at_first_missing(self):
        actual = json_schema(DataClassWithOptionalNested, allow_missing=True).load('{"x": null}')
        assert actual == DataClassWithOptionalNested(None)

    def test_error_when_missing_required(self):
        with pytest.raises(LoadError) as exc_info:
            json_schema(DataClassWithDataClass, allow_missing=False).load('{"dc_with_list": {}}')
        assert 'dc_with_list' in exc_info.value.message
        assert 'xs' in exc_info.value.message

    def test_error_when_missing_required_by_default(self):
        with pytest.raises(LoadError) as exc_info:
            json_schema(DataClassWithDataClass).load('{"dc_with_list": {}}')
        assert 'dc_with_list' in exc_info.value.message
        assert 'xs' in exc_info.value.message


class TestAllowUnexpected:
    def test_allow_unexpected(self):
        actual = json_schema(DataClassWithOptional, allow_unexpected=True).load('{"x": null, "y": true}')
        assert actual == DataClassWithOptional(None)

    def test_allow_unexpected_is_recursive(self):
        actual = json_schema(DataClassWithOptionalNested, allow_unexpected=True).load('{"x": {"x": null, "y": "test"}}')
        expected = DataClassWithOptionalNested(DataClassWithOptional(None))
        assert actual == expected

    def test_error_when_unexpected(self):
        with pytest.raises(LoadError) as exc_info:
            json_schema(DataClassWithOptional, allow_unexpected=False).load('{"x": 1, "y": 1}')
        assert '"y"' in exc_info.value.message

    def test_error_when_unexpected_by_default(self):
        with pytest.raises(LoadError) as exc_info:
            json_schema(DataClassWithOptional).load('{"x": 1, "y": 1}')
        assert '"y"' in exc_info.value.message
