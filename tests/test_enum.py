from dataclasses import dataclass
from datetime import date
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


@dataclass(frozen=True)
class DataWithEnum:
    name: str
    enum: Symbol = Symbol.GAMMA


class TestEnum:
    def setup(self):
        self.schema = JsonSchema(DataWithEnum)

    def test_load(self):
        enum = DataWithEnum('name1', Symbol.ALPHA)
        enum_json = '{"name": "name1", "enum": "alpha"}'
        assert self.schema.load(enum_json) == enum

        int_enum = DataWithEnum('name1', Symbol.ONE)
        int_enum_json = '{"name": "name1", "enum": 1}'
        assert self.schema.load(int_enum_json) == int_enum

        float_enum = DataWithEnum('name1', Symbol.PI)
        float_enum_json = '{"name": "name1", "enum": 3.14}'
        assert self.schema.load(float_enum_json) == float_enum

    def test_dump(self):
        enum = DataWithEnum('name1', Symbol.ALPHA)
        enum_json = '{"name": "name1", "enum": "alpha"}'
        assert self.schema.dump(enum) == enum_json

        int_enum = DataWithEnum('name1', Symbol.ONE)
        int_enum_json = '{"name": "name1", "enum": 1}'
        assert self.schema.dump(int_enum) == int_enum_json

        float_enum = DataWithEnum('name1', Symbol.PI)
        float_enum_json = '{"name": "name1", "enum": 3.14}'
        assert self.schema.dump(float_enum) == float_enum_json

    def test_default(self):
        schema = JsonSchema(DataWithEnum)

        json = '{"name": "name2", "enum": "gamma"}'
        assert schema.dump(DataWithEnum('name2')) == json

        enum_from_json = schema.load(json)
        json_from_enum = schema.dump(enum_from_json)
        assert json_from_enum == json


class Gender(str, Enum):
    MALE = 'male'
    FEMALE = 'female'
    OTHER = 'other'
    NA = 'not specified'


@dataclass(frozen=True)
class Profile:
    gender: Gender = Gender.NA


class TestStrEnum:
    def setup(self):
        self.schema = JsonSchema(Profile)
        self.json = '{"gender": "male"}'
        self.dataclass = Profile(Gender.MALE)

    def test_load(self):
        actual = self.schema.load(self.json)
        assert actual == self.dataclass

    def test_dump(self):
        actual = self.schema.dump(self.dataclass)
        assert actual == self.json

    def test_load_with_invalid_enum_value(self):
        schema = JsonSchema(Profile)
        with pytest.raises(LoadError):
            schema.load('{"gender": "python"}')


@dataclass(frozen=True)
class EnumContainer:
    enum_list: List[Symbol]
    enum_mapping: Dict[str, Symbol]


class TestEnumCollection:
    def setup(self):
        self.schema = JsonSchema(EnumContainer)
        self.json = '{"enum_list": ["gamma", 1], "enum_mapping": {"first": "alpha", "second": 3.14}}'
        self.dataclass = EnumContainer(
            enum_list=[Symbol.GAMMA, Symbol.ONE],
            enum_mapping={"first": Symbol.ALPHA, "second": Symbol.PI}
        )

    def test_load(self):
        actual = self.schema.load(self.json)
        assert actual == self.dataclass

    def test_dump(self):
        actual = self.schema.dump(self.dataclass)
        assert actual == self.json


class Permission(IntFlag):
    READ = 4
    WRITE = 2
    EXECUTE = 1


@dataclass(frozen=True)
class File:
    name: str
    permission: Permission


class TestIntFlag:
    def setup(self):
        self.schema = DictSchema(File)
        f_name = 'readme.txt'
        self.dict = {'name': f_name, 'permission': 7}
        self.dataclass = File(f_name, Permission.READ | Permission.WRITE | Permission.EXECUTE)

    def test_load(self):
        actual = self.schema.load(self.dict)
        assert actual == self.dataclass

    def test_dump(self):
        actual = self.schema.dump(self.dataclass)
        assert actual == self.dict


class Date(date, Enum):
    TRINITY = 1945, 6, 16
    GAGARIN = 1961, 4, 11


@dataclass(frozen=True)
class HistoricEvent:
    name: str
    date: Date


class TestDateEnum:
    def setup(self):
        self.schema = DictSchema(HistoricEvent)
        name = 'First Man in Space'
        self.dict = {'name': name, 'date': '1961-04-11'}
        self.dataclass = HistoricEvent(name, Date.GAGARIN)

    def test_load(self):
        actual = self.schema.load(self.dict)
        assert actual == self.dataclass
        assert isinstance(actual.date, Date)

    def test_dump(self):
        actual = self.schema.dump(self.dataclass)
        assert actual == self.dict
