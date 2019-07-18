from dataclasses import dataclass
from enum import Enum, IntFlag
from typing import Dict, List

import pytest

from serious.dict import DictSchema
from serious.errors import LoadError
from serious.json import JsonSchema


class Symbol(Enum):
    ALPHA = "alpha"
    BETA = "beta"
    GAMMA = "gamma"
    ONE = 1
    PI = 3.14


class Gender(str, Enum):
    MALE = 'male'
    FEMALE = 'female'
    OTHER = 'other'
    NA = 'not specified'


@dataclass(frozen=True)
class DataWithEnum:
    name: str
    enum: Symbol = Symbol.GAMMA


@dataclass(frozen=True)
class Profile:
    gender: Gender = Gender.NA


@dataclass(frozen=True)
class EnumContainer:
    enum_list: List[Symbol]
    enum_mapping: Dict[str, Symbol]


class TestEncoder:

    def test_data_with_enum(self):
        schema = JsonSchema(DataWithEnum)

        enum = DataWithEnum('name1', Symbol.ALPHA)
        enum_json = '{"name": "name1", "enum": "alpha"}'
        assert schema.dump(enum) == enum_json

        int_enum = DataWithEnum('name1', Symbol.ONE)
        int_enum_json = '{"name": "name1", "enum": 1}'
        assert schema.dump(int_enum) == int_enum_json

        float_enum = DataWithEnum('name1', Symbol.PI)
        float_enum_json = '{"name": "name1", "enum": 3.14}'
        assert schema.dump(float_enum) == float_enum_json

    def test_data_with_str_enum(self):
        schema = JsonSchema(Profile)
        o = Profile(Gender.MALE)
        assert schema.dump(o) == '{"gender": "male"}'

    def test_data_with_enum_default_value(self):
        schema = JsonSchema(DataWithEnum)
        enum_to_json = schema.dump(DataWithEnum('name2'))
        assert enum_to_json == '{"name": "name2", "enum": "gamma"}'

    def test_collection_with_enum(self):
        schema = JsonSchema(EnumContainer)
        container = EnumContainer(
            enum_list=[Symbol.GAMMA, Symbol.ONE],
            enum_mapping={"first": Symbol.ALPHA, "second": Symbol.PI}
        )
        json = '{"enum_list": ["gamma", 1], "enum_mapping": {"first": "alpha", "second": 3.14}}'
        assert schema.dump(container) == json


class TestDecoder:

    def test_data_with_enum(self):
        schema = JsonSchema(DataWithEnum)

        enum = DataWithEnum('name1', Symbol.ALPHA)
        enum_json = '{"name": "name1", "enum": "alpha"}'

        enum_from_json = schema.load(enum_json)
        assert enum == enum_from_json
        assert schema.dump(enum_from_json) == enum_json

        int_enum = DataWithEnum('name1', Symbol.ONE)
        int_enum_json = '{"name": "name1", "enum": 1}'
        int_enum_from_json = schema.load(int_enum_json)
        assert int_enum == int_enum_from_json
        assert schema.dump(int_enum_from_json) == int_enum_json

        float_enum = DataWithEnum('name1', Symbol.PI)
        float_enum_json = '{"name": "name1", "enum": 3.14}'
        float_enum_from_json = schema.load(float_enum_json)
        assert float_enum == float_enum_from_json
        assert schema.dump(float_enum_from_json) == float_enum_json

    def test_data_with_str_enum(self):
        schema = JsonSchema(Profile)
        json = '{"gender": "male"}'
        o = schema.load(json)
        assert Profile(Gender.MALE) == o
        assert schema.dump(o) == json

    def test_data_with_invalid_data(self):
        schema = JsonSchema(Profile)
        with pytest.raises(LoadError):
            schema.load('{"gender": "python"}')

    def test_data_with_enum_default_value(self):
        schema = JsonSchema(DataWithEnum)

        json = '{"name": "name2", "enum": "gamma"}'
        assert schema.dump(DataWithEnum('name2')) == json

        enum_from_json = schema.load(json)
        json_from_enum = schema.dump(enum_from_json)
        assert json_from_enum == json

    def test_collection_with_enum(self):
        json = '{"enum_list": ["gamma", 1], "enum_mapping": {"first": "alpha", "second": 3.14}}'
        schema = JsonSchema(EnumContainer)
        container_from_json = schema.load(json)
        o = EnumContainer(
            enum_list=[Symbol.GAMMA, Symbol.ONE],
            enum_mapping={"first": Symbol.ALPHA, "second": Symbol.PI}
        )
        assert o == container_from_json
        assert schema.dump(container_from_json) == json
