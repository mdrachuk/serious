from dataclasses import dataclass
from typing import Optional, Any
from uuid import UUID

import pytest

from serious.context import SerializationContext
from serious.errors import LoadError
from serious.field_serializers import FieldSerializer
from serious.json import json_schema
from serious.json.api import JsonSchema, Loading, Dumping
from serious.serializer_options import SerializerOption
from serious.utils import Primitive
from tests.entities import (DataClassWithDataClass, DataClassWithOptional,
                            DataClassWithOptionalNested, DataClassWithUuid)


@dataclass
class UserId:
    value: int


@dataclass(frozen=True)
class User:
    id: UserId
    username: str
    password: str
    age: Optional[int]


class UserIdSerializer(FieldSerializer):
    def dump(self, value: Any, ctx: SerializationContext) -> Primitive:
        return value.value

    def load(self, value: Primitive, ctx: SerializationContext) -> Any:
        return UserId(value)


class TestDefaults:
    schema = json_schema(User)

    def test_invalid_class(self):
        with pytest.raises(TypeError):
            JsonSchema(dict, [], Loading(), Dumping())

    def test_dump(self):
        user = User(id=UserId(0), username='admin', password='admin', age=None)
        d = self.schema.dump(user)
        assert d == '{"id": {"value": 0}, "username": "admin", "password": "admin", "age": null}'

    def test_load(self):
        user = self.schema.load('{"id": {"value": 0}, "username": "admin", "password": "admin", "age": null}')
        assert user == User(id=UserId(0), username='admin', password='admin', age=None)

    def test_dump_many(self):
        user1 = User(id=UserId(0), username='admin', password='admin', age=None)
        user2 = User(id=UserId(1), username='root', password='root123', age=23)
        expected = '[{"id": {"value": 0}, "username": "admin", "password": "admin", "age": null}, ' \
                   '{"id": {"value": 1}, "username": "root", "password": "root123", "age": 23}]'
        actual = self.schema.dump_many([user1, user2])
        assert actual == expected

    def test_load_many(self):
        expected = [User(id=UserId(0), username='admin', password='admin', age=None),
                    User(id=UserId(1), username='root', password='root123', age=23)]
        data = '[{"id": {"value": 0}, "username": "admin", "password": "admin", "age": null},' \
               '{"id": {"value": 1}, "username": "root", "password": "root123", "age": 23}]'
        actual = self.schema.load_many(data)
        assert actual == expected


class TestSerializer:
    serializers = SerializerOption.defaults()
    serializers.insert(0, SerializerOption(lambda attr: attr.type is UserId, factory=UserIdSerializer))
    schema = JsonSchema(User, serializers, Loading(), Dumping())

    def test_dump(self):
        actual = self.schema.dump(User(id=UserId(0), username='admin', password='admin', age=None))
        expected = '{"id": 0, "username": "admin", "password": "admin", "age": null}'
        assert actual == expected

    def test_load(self):
        actual = self.schema.load('{"id": 0, "username": "admin", "password": "admin", "age": null}')
        expected = User(id=UserId(0), username='admin', password='admin', age=None)
        assert actual == expected


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
