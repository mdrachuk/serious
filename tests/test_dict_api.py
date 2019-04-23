from uuid import UUID

import pytest

from serious.dict import schema, Loading
from tests.entities import (DataClassJsonDecorator, DataClassWithDataClass, DataClassWithOptional,
                            DataClassWithOptionalNested, DataClassWithUuid)

allow_missing = Loading(allow_missing=True)


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


class TestInferMissing:
    def test_infer_missing(self):
        actual = schema(DataClassWithOptional, load=allow_missing).load({})
        assert actual == DataClassWithOptional(None)

    def test_infer_missing_is_recursive(self):
        actual = schema(DataClassWithOptionalNested, load=allow_missing).load({"x": {}})
        expected = DataClassWithOptionalNested(DataClassWithOptional(None))
        assert actual == expected

    def test_infer_missing_terminates_at_first_missing(self):
        actual = schema(DataClassWithOptionalNested, load=allow_missing).load({"x": None})
        assert actual == DataClassWithOptionalNested(None)


class TestWarnings:
    def test_warns_when_nonoptional_field_is_missing_with_infer_missing(self):
        with pytest.warns(RuntimeWarning, match='Missing value'):
            schema(DataClassWithDataClass, load=allow_missing).load({"dc_with_list": {}})

    def test_warns_when_required_field_is_none(self):
        with pytest.warns(RuntimeWarning, match='`NoneType` object'):
            schema(DataClassWithDataClass).load({"dc_with_list": None})


class TestErrors:
    def test_error_when_nonoptional_field_is_missing(self):
        with pytest.raises(KeyError):
            schema(DataClassWithDataClass).load({"dc_with_list": {}})


class TestDecorator:
    def test_decorator(self):
        data = {"x": "x"}
        s = schema(DataClassJsonDecorator)
        o = s.load(data)
        assert s.dump(o) == data
