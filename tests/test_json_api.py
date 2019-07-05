from dataclasses import dataclass
from typing import Optional, Any
from uuid import UUID

import pytest

from serious.context import SerializationContext
from serious.descriptors import FieldDescriptor
from serious.errors import LoadError
from serious.field_serializers import FieldSerializer
from serious.json.api import JsonSerializer
from serious.serializer import DataclassSerializer
from serious.serializer_options import FieldSerializerOption
from serious.utils import Primitive
from tests.entities import (DataclassWithDataclass, DataclassWithOptional,
                            DataclassWithOptionalNested, DataclassWithUuid)


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

    def setup_class(self):
        self.schema = JsonSerializer(User)

    def test_invalid_class(self):
        with pytest.raises(TypeError):
            JsonSerializer(dict, field_serializers=[])

    def test_load(self):
        user = self.schema.load('{"id": {"value": 0}, "username": "admin", "password": "admin", "age": null}')
        assert user == User(id=UserId(0), username='admin', password='admin', age=None)

    def test_load_many(self):
        expected = [User(id=UserId(0), username='admin', password='admin', age=None),
                    User(id=UserId(1), username='root', password='root123', age=23)]
        data = '[{"id": {"value": 0}, "username": "admin", "password": "admin", "age": null},' \
               '{"id": {"value": 1}, "username": "root", "password": "root123", "age": 23}]'
        actual = self.schema.load_many(data)
        assert actual == expected

    def test_dump(self):
        user = User(id=UserId(0), username='admin', password='admin', age=None)
        d = self.schema.dump(user)
        assert d == '{"id": {"value": 0}, "username": "admin", "password": "admin", "age": null}'

    def test_dump_many(self):
        user1 = User(id=UserId(0), username='admin', password='admin', age=None)
        user2 = User(id=UserId(1), username='root', password='root123', age=23)
        expected = '[{"id": {"value": 0}, "username": "admin", "password": "admin", "age": null}, ' \
                   '{"id": {"value": 1}, "username": "root", "password": "root123", "age": 23}]'
        actual = self.schema.dump_many([user1, user2])
        assert actual == expected


class UserIdSerializerOption(FieldSerializerOption):

    def fits(self, field: FieldDescriptor) -> bool:
        return field.type is UserId

    def create(self, field: FieldDescriptor, sr: DataclassSerializer) -> FieldSerializer:
        return UserIdSerializer(field)


class TestSerializer:

    def setup_class(self):
        serializers = FieldSerializerOption.defaults()
        serializers.insert(0, UserIdSerializerOption())
        self.schema = JsonSerializer(User, field_serializers=serializers)

    def test_dump(self):
        actual = self.schema.dump(User(id=UserId(0), username='admin', password='admin', age=None))
        expected = '{"id": {"value": 0}, "username": "admin", "password": "admin", "age": null}'
        assert actual == expected

    def test_load(self):
        actual = self.schema.load('{"id": {"value": 0}, "username": "admin", "password": "admin", "age": null}')
        expected = User(id=UserId(0), username='admin', password='admin', age=None)
        assert actual == expected


class TestTypes:
    def setup_class(self):
        self.uuid_s = 'd1d61dd7-c036-47d3-a6ed-91cc2e885fc8'
        self.dc_uuid_json = f'{{"id": "{self.uuid_s}"}}'
        self.uuid_schema = JsonSerializer(DataclassWithUuid)

    def test_uuid_decode(self):
        actual = self.uuid_schema.load(self.dc_uuid_json)
        assert actual == DataclassWithUuid(UUID(self.uuid_s))

    def test_uuid_encode(self):
        actual = self.uuid_schema.dump(DataclassWithUuid(UUID(self.uuid_s)))
        assert actual == self.dc_uuid_json


class TestAllowMissing:
    def test_allow_missing(self):
        actual = JsonSerializer(DataclassWithOptional, allow_missing=True).load('{}')
        assert actual == DataclassWithOptional(None)

    def test_allow_unexpected_is_recursive(self):
        actual = JsonSerializer(DataclassWithOptionalNested, allow_missing=True).load('{"x": {}}')
        expected = DataclassWithOptionalNested(DataclassWithOptional(None))
        assert actual == expected

    def test_allow_missing_terminates_at_first_missing(self):
        actual = JsonSerializer(DataclassWithOptionalNested, allow_missing=True).load('{"x": null}')
        assert actual == DataclassWithOptionalNested(None)

    def test_error_when_missing_required(self):
        with pytest.raises(LoadError) as exc_info:
            JsonSerializer(DataclassWithDataclass, allow_missing=False).load('{"dc_with_list": {}}')
        assert 'dc_with_list' in exc_info.value.message
        assert 'xs' in exc_info.value.message

    def test_error_when_missing_required_by_default(self):
        with pytest.raises(LoadError) as exc_info:
            JsonSerializer(DataclassWithDataclass).load('{"dc_with_list": {}}')
        assert 'dc_with_list' in exc_info.value.message
        assert 'xs' in exc_info.value.message


class TestAllowUnexpected:
    def test_allow_unexpected(self):
        actual = JsonSerializer(DataclassWithOptional, allow_unexpected=True).load('{"x": null, "y": true}')
        assert actual == DataclassWithOptional(None)

    def test_allow_unexpected_is_recursive(self):
        actual = JsonSerializer(DataclassWithOptionalNested, allow_unexpected=True).load(
            '{"x": {"x": null, "y": "test"}}')
        expected = DataclassWithOptionalNested(DataclassWithOptional(None))
        assert actual == expected

    def test_error_when_unexpected(self):
        with pytest.raises(LoadError) as exc_info:
            JsonSerializer(DataclassWithOptional, allow_unexpected=False).load('{"x": 1, "y": 1}')
        assert '"y"' in exc_info.value.message

    def test_error_when_unexpected_by_default(self):
        with pytest.raises(LoadError) as exc_info:
            JsonSerializer(DataclassWithOptional).load('{"x": 1, "y": 1}')
        assert '"y"' in exc_info.value.message
