from uuid import UUID

import pytest

import m2
from tests.entities import (DataClassJsonDecorator, DataClassWithDataClass, DataClassWithOptional,
                            DataClassWithOptionalNested, DataClassWithUuid)


class TestTypes:
    uuid_s = 'd1d61dd7-c036-47d3-a6ed-91cc2e885fc8'
    dc_uuid_json = f'{{"id": "{uuid_s}"}}'

    def test_uuid_encode(self):
        actual = m2.asjson(DataClassWithUuid(UUID(self.uuid_s)))
        assert actual == self.dc_uuid_json

    def test_uuid_decode(self):
        actual = m2.load(DataClassWithUuid).from_(self.dc_uuid_json)
        assert actual == DataClassWithUuid(UUID(self.uuid_s))


class TestInferMissing:
    def test_infer_missing(self):
        actual = m2.load(DataClassWithOptional, infer_missing=True).from_('{}')
        assert actual == DataClassWithOptional(None)

    def test_infer_missing_is_recursive(self):
        actual = m2.load(DataClassWithOptionalNested, infer_missing=True).from_('{"x": {}}')
        expected = DataClassWithOptionalNested(DataClassWithOptional(None))
        assert actual == expected

    def test_infer_missing_terminates_at_first_missing(self):
        actual = m2.load(DataClassWithOptionalNested, infer_missing=True).from_('{"x": null}')
        assert actual == DataClassWithOptionalNested(None)


class TestWarnings:
    def test_warns_when_nonoptional_field_is_missing_with_infer_missing(self):
        with pytest.warns(RuntimeWarning, match='Missing value'):
            m2.load(DataClassWithDataClass, infer_missing=True).from_('{"dc_with_list": {}}')

    def test_warns_when_required_field_is_none(self):
        with pytest.warns(RuntimeWarning, match='`NoneType` object'):
            m2.load(DataClassWithDataClass).from_('{"dc_with_list": null}')


class TestErrors:
    def test_error_when_nonoptional_field_is_missing(self):
        with pytest.raises(KeyError):
            m2.load(DataClassWithDataClass).from_('{"dc_with_list": {}}')


class TestDecorator:
    def test_decorator(self):
        json_s = '{"x": "x"}'
        o = m2.load(DataClassJsonDecorator).from_(json_s)
        assert m2.asjson(o) == json_s
