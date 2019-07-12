from dataclasses import dataclass
from enum import Enum
from typing import Dict, List

from serious.json import JsonSchema


class MyEnum(Enum):
    STR1 = "str1"
    STR2 = "str2"
    STR3 = "str3"
    INT1 = 1
    FLOAT1 = 1.23


class MyStrEnum(str, Enum):
    STR1 = "str1"


@dataclass(frozen=True)
class DataWithEnum:
    name: str
    my_enum: MyEnum = MyEnum.STR3


@dataclass(frozen=True)
class DataWithStrEnum:
    my_str_enum: MyStrEnum = MyEnum.STR1


@dataclass(frozen=True)
class EnumContainer:
    enum_list: List[MyEnum]
    dict_enum_value: Dict[str, MyEnum]


class TestEncoder:

    def test_data_with_enum(self):
        schema = JsonSchema(DataWithEnum)

        enum = DataWithEnum('name1', MyEnum.STR1)
        enum_json = '{"name": "name1", "my_enum": "str1"}'
        assert schema.dump(enum) == enum_json

        int_enum = DataWithEnum('name1', MyEnum.INT1)
        int_enum_json = '{"name": "name1", "my_enum": 1}'
        assert schema.dump(int_enum) == int_enum_json

        float_enum = DataWithEnum('name1', MyEnum.FLOAT1)
        float_enum_json = '{"name": "name1", "my_enum": 1.23}'
        assert schema.dump(float_enum) == float_enum_json

    def test_data_with_str_enum(self):
        schema = JsonSchema(DataWithStrEnum)
        o = DataWithStrEnum(MyStrEnum.STR1)
        assert schema.dump(o) == '{"my_str_enum": "str1"}'

    def test_data_with_enum_default_value(self):
        schema = JsonSchema(DataWithEnum)
        enum_to_json = schema.dump(DataWithEnum('name2'))
        assert enum_to_json == '{"name": "name2", "my_enum": "str3"}'

    def test_collection_with_enum(self):
        schema = JsonSchema(EnumContainer)
        container = EnumContainer(
            enum_list=[MyEnum.STR3, MyEnum.INT1],
            dict_enum_value={"key1str": MyEnum.STR1, "key1float": MyEnum.FLOAT1}
        )
        json = '{"enum_list": ["str3", 1], "dict_enum_value": {"key1str": "str1", "key1float": 1.23}}'
        assert schema.dump(container) == json


class TestDecoder:

    def test_data_with_enum(self):
        schema = JsonSchema(DataWithEnum)

        enum = DataWithEnum('name1', MyEnum.STR1)
        enum_json = '{"name": "name1", "my_enum": "str1"}'

        enum_from_json = schema.load(enum_json)
        assert enum == enum_from_json
        assert schema.dump(enum_from_json) == enum_json

        int_enum = DataWithEnum('name1', MyEnum.INT1)
        int_enum_json = '{"name": "name1", "my_enum": 1}'
        int_enum_from_json = schema.load(int_enum_json)
        assert int_enum == int_enum_from_json
        assert schema.dump(int_enum_from_json) == int_enum_json

        float_enum = DataWithEnum('name1', MyEnum.FLOAT1)
        float_enum_json = '{"name": "name1", "my_enum": 1.23}'
        float_enum_from_json = schema.load(float_enum_json)
        assert float_enum == float_enum_from_json
        assert schema.dump(float_enum_from_json) == float_enum_json

    def test_data_with_str_enum(self):
        schema = JsonSchema(DataWithStrEnum)
        json = '{"my_str_enum": "str1"}'
        o = schema.load(json)
        assert DataWithStrEnum(MyStrEnum.STR1) == o
        assert schema.dump(o) == json

    def test_data_with_enum_default_value(self):
        schema = JsonSchema(DataWithEnum)

        json = '{"name": "name2", "my_enum": "str3"}'
        assert schema.dump(DataWithEnum('name2')) == json

        enum_from_json = schema.load(json)
        json_from_enum = schema.dump(enum_from_json)
        assert json_from_enum == json

    def test_collection_with_enum(self):
        json = '{"enum_list": ["str3", 1], "dict_enum_value": {"key1str": "str1", "key1float": 1.23}}'
        schema = JsonSchema(EnumContainer)
        container_from_json = schema.load(json)
        o = EnumContainer(
            enum_list=[MyEnum.STR3, MyEnum.INT1],
            dict_enum_value={"key1str": MyEnum.STR1, "key1float": MyEnum.FLOAT1}
        )
        assert o == container_from_json
        assert schema.dump(container_from_json) == json
