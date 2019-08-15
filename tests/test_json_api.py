from dataclasses import dataclass
from typing import Optional
from uuid import UUID

import pytest

from serious import JsonModel, LoadError
from serious.descriptors import TypeDescriptor
from serious.serialization import Loading, Dumping, FieldSerializer, field_serializers
from tests.entities import DataclassWithDataclass, DataclassWithOptional, DataclassWithOptionalNested, DataclassWithUuid


@dataclass
class UserId:
    value: int


@dataclass(frozen=True)
class User:
    id: UserId
    username: str
    password: str
    age: Optional[int]


class TestDefaults:

    def setup_class(self):
        self.model = JsonModel(User)

    def test_invalid_class(self):
        with pytest.raises(AssertionError):
            JsonModel(dict, serializers=[])

    def test_load(self):
        user = self.model.load('{"id": {"value": 0}, "username": "admin", "password": "admin", "age": null}')
        assert user == User(id=UserId(0), username='admin', password='admin', age=None)

    def test_load_many(self):
        expected = [User(id=UserId(0), username='admin', password='admin', age=None),
                    User(id=UserId(1), username='root', password='root123', age=23)]
        data = '[{"id": {"value": 0}, "username": "admin", "password": "admin", "age": null},' \
               '{"id": {"value": 1}, "username": "root", "password": "root123", "age": 23}]'
        actual = self.model.load_many(data)
        assert actual == expected

    def test_dump(self):
        user = User(id=UserId(0), username='admin', password='admin', age=None)
        d = self.model.dump(user)
        assert d == '{"id": {"value": 0}, "username": "admin", "password": "admin", "age": null}'

    def test_dump_many(self):
        user1 = User(id=UserId(0), username='admin', password='admin', age=None)
        user2 = User(id=UserId(1), username='root', password='root123', age=23)
        expected = '[{"id": {"value": 0}, "username": "admin", "password": "admin", "age": null}, ' \
                   '{"id": {"value": 1}, "username": "root", "password": "root123", "age": 23}]'
        actual = self.model.dump_many([user1, user2])
        assert actual == expected


class UserIdSerializer(FieldSerializer[UserId, int]):

    def load(self, value: int, ctx: Loading) -> UserId:
        return UserId(value)

    def dump(self, value: UserId, ctx: Dumping) -> int:
        return value.value

    @classmethod
    def fits(cls, desc: TypeDescriptor) -> bool:
        return desc.cls is UserId


class TestSerializer:

    def setup_class(self):
        serializers = field_serializers([UserIdSerializer])
        self.model = JsonModel(User, serializers=serializers)

    def test_dump(self):
        actual = self.model.dump(User(id=UserId(0), username='admin', password='admin', age=None))
        expected = '{"id": 0, "username": "admin", "password": "admin", "age": null}'
        assert actual == expected

    def test_load(self):
        actual = self.model.load('{"id": 0, "username": "admin", "password": "admin", "age": null}')
        expected = User(id=UserId(0), username='admin', password='admin', age=None)
        assert actual == expected


class TestTypes:
    def setup_class(self):
        self.uuid_s = 'd1d61dd7-c036-47d3-a6ed-91cc2e885fc8'
        self.dc_uuid_json = f'{{"id": "{self.uuid_s}"}}'
        self.uuid_model = JsonModel(DataclassWithUuid)

    def test_uuid_decode(self):
        actual = self.uuid_model.load(self.dc_uuid_json)
        assert actual == DataclassWithUuid(UUID(self.uuid_s))

    def test_uuid_encode(self):
        actual = self.uuid_model.dump(DataclassWithUuid(UUID(self.uuid_s)))
        assert actual == self.dc_uuid_json


class TestAllowMissing:
    def test_allow_missing(self):
        actual = JsonModel(DataclassWithOptional, allow_missing=True).load('{}')
        assert actual == DataclassWithOptional(None)

    def test_allow_unexpected_is_recursive(self):
        actual = JsonModel(DataclassWithOptionalNested, allow_missing=True).load('{"x": {}}')
        expected = DataclassWithOptionalNested(DataclassWithOptional(None))
        assert actual == expected

    def test_allow_missing_terminates_at_first_missing(self):
        actual = JsonModel(DataclassWithOptionalNested, allow_missing=True).load('{"x": null}')
        assert actual == DataclassWithOptionalNested(None)

    def test_error_when_missing_required(self):
        with pytest.raises(LoadError) as exc_info:
            JsonModel(DataclassWithDataclass, allow_missing=False).load('{"dc_with_list": {}}')
        assert 'dc_with_list' in exc_info.value.message
        assert 'xs' in exc_info.value.message

    def test_error_when_missing_required_by_default(self):
        with pytest.raises(LoadError) as exc_info:
            JsonModel(DataclassWithDataclass).load('{"dc_with_list": {}}')
        assert 'dc_with_list' in exc_info.value.message
        assert 'xs' in exc_info.value.message


class TestAllowUnexpected:
    def test_allow_unexpected(self):
        actual = JsonModel(DataclassWithOptional, allow_unexpected=True).load('{"x": null, "y": true}')
        assert actual == DataclassWithOptional(None)

    def test_allow_unexpected_is_recursive(self):
        actual = JsonModel(DataclassWithOptionalNested, allow_unexpected=True).load(
            '{"x": {"x": null, "y": "test"}}')
        expected = DataclassWithOptionalNested(DataclassWithOptional(None))
        assert actual == expected

    def test_error_when_unexpected(self):
        with pytest.raises(LoadError) as exc_info:
            JsonModel(DataclassWithOptional, allow_unexpected=False).load('{"x": 1, "y": 1}')
        assert '"y"' in exc_info.value.message

    def test_error_when_unexpected_by_default(self):
        with pytest.raises(LoadError) as exc_info:
            JsonModel(DataclassWithOptional).load('{"x": 1, "y": 1}')
        assert '"y"' in exc_info.value.message
