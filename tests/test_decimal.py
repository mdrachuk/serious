from dataclasses import dataclass
from decimal import Decimal
from enum import Enum

from serious.dict import dict_schema
from serious.json import json_schema


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


enum_schema = json_schema(DataWithEnum)

d1 = DataWithEnum('name1', MyEnum.STR1)
d1_json = '{"name": "name1", "my_enum": "str1"}'

# Make sure the enum is set to the default value defined by MyEnum
d2_using_default_value = DataWithEnum('name2')
d2_json = '{"name": "name2", "my_enum": "str3"}'

d3_int = DataWithEnum('name1', MyEnum.INT1)
d3_int_json = '{"name": "name1", "my_enum": 1}'
d4_float = DataWithEnum('name1', MyEnum.FLOAT1)
d4_float_json = '{"name": "name1", "my_enum": 1.23}'


@dataclass(frozen=True)
class Person:
    name: str
    height: Decimal


str_enum_schema = json_schema(Person)

person = Person('Keith', Decimal('1.76'))
person_dict = dict(name='Keith', height='1.76')


class TestDecimal:
    def test_load(self):
        actual = dict_schema(Person).load(person_dict)
        assert actual == person

    def test_dump(self):
        actual = dict_schema(Person).dump(person)
        assert actual == person_dict
