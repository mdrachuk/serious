from uuid import UUID

import pytest

from serious.errors import LoadError
from serious.json import schema, Loading
from tests.entities import (DataClassJsonDecorator, DataClassWithDataClass, DataClassWithOptional,
                            DataClassWithOptionalNested, DataClassWithUuid)

allow_missing = Loading(allow_missing=True)


class TestTypes:
    uuid_s = 'd1d61dd7-c036-47d3-a6ed-91cc2e885fc8'
    dc_uuid_json = f'{{"id": "{uuid_s}"}}'
    uuid_schema = schema(DataClassWithUuid)

    def test_uuid_encode(self):
        actual = self.uuid_schema.dump(DataClassWithUuid(UUID(self.uuid_s)))
        assert actual == self.dc_uuid_json

    def test_uuid_decode(self):
        actual = self.uuid_schema.load(self.dc_uuid_json)
        assert actual == DataClassWithUuid(UUID(self.uuid_s))


class TestInferMissing:
    def test_infer_missing(self):
        actual = schema(DataClassWithOptional, load=allow_missing).load('{}')
        assert actual == DataClassWithOptional(None)

    def test_infer_missing_is_recursive(self):
        actual = schema(DataClassWithOptionalNested, load=allow_missing).load('{"x": {}}')
        expected = DataClassWithOptionalNested(DataClassWithOptional(None))
        assert actual == expected

    def test_infer_missing_terminates_at_first_missing(self):
        actual = schema(DataClassWithOptionalNested, load=allow_missing).load('{"x": null}')
        assert actual == DataClassWithOptionalNested(None)


class TestErrors:
    def test_error_when_nonoptional_field_is_missing(self):
        with pytest.raises(LoadError) as exc_info:
            schema(DataClassWithDataClass).load('{"dc_with_list": {}}')
        assert 'dc_with_list' in exc_info.value.message
        assert 'xs' in exc_info.value.message


class TestDecorator:
    def test_decorator(self):
        json_s = '{"x": "x"}'
        s = schema(DataClassJsonDecorator)
        o = s.load(json_s)
        assert s.dump(o) == json_s
