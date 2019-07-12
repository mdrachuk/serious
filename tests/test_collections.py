from collections import deque

from serious.json import JsonSerializer
from tests.entities import (DataclassIntImmutableDefault,
                            DataclassMutableDefaultDict,
                            DataclassMutableDefaultList, DataclassWithDeque,
                            DataclassWithDict, DataclassWithDictInt,
                            DataclassWithFrozenSet, DataclassWithList,
                            DataclassWithListStr, DataclassWithOptional,
                            DataclassWithOptionalStr, DataclassWithSet,
                            DataclassWithTuple, DataclassWithUnionIntNone)


class TestEncoder:
    def test_list(self):
        assert JsonSerializer(DataclassWithList).dump(DataclassWithList([1])) == '{"xs": [1]}'

    def test_list_str(self):
        assert JsonSerializer(DataclassWithListStr).dump(DataclassWithListStr(['1'])) == '{"xs": ["1"]}'

    def test_dict(self):
        assert JsonSerializer(DataclassWithDict).dump(DataclassWithDict({'1': 'a'})) == '{"kvs": {"1": "a"}}'

    def test_dict_int(self):
        assert JsonSerializer(DataclassWithDictInt).dump(DataclassWithDictInt({1: 'a'})) == '{"kvs": {"1": "a"}}'

    def test_set(self):
        assert JsonSerializer(DataclassWithSet).dump(DataclassWithSet({1})) == '{"xs": [1]}'

    def test_tuple(self):
        assert JsonSerializer(DataclassWithTuple).dump(DataclassWithTuple((1,))) == '{"xs": [1]}'

    def test_frozenset(self):
        assert JsonSerializer(DataclassWithFrozenSet).dump(DataclassWithFrozenSet(frozenset([1]))) == '{"xs": [1]}'

    def test_deque(self):
        assert JsonSerializer(DataclassWithDeque).dump(DataclassWithDeque(deque([1]))) == '{"xs": [1]}'

    def test_optional(self):
        s = JsonSerializer(DataclassWithOptional)
        assert s.dump(DataclassWithOptional(1)) == '{"x": 1}'
        assert s.dump(DataclassWithOptional(None)) == '{"x": null}'

    def test_optional_str(self):
        s = JsonSerializer(DataclassWithOptionalStr)
        assert s.dump(DataclassWithOptionalStr('1')) == '{"x": "1"}'
        assert s.dump(DataclassWithOptionalStr(None)) == '{"x": null}'
        assert s.dump(DataclassWithOptionalStr()) == '{"x": null}'

    def test_union_int_none(self):
        s = JsonSerializer(DataclassWithUnionIntNone)
        assert s.dump(DataclassWithUnionIntNone(1)) == '{"x": 1}'
        assert s.dump(DataclassWithUnionIntNone(None)) == '{"x": null}'

    def test_immutable_default(self):
        assert JsonSerializer(DataclassIntImmutableDefault).dump(DataclassIntImmutableDefault()) == '{"x": 0}'

    def test_mutable_default_list(self):
        assert JsonSerializer(DataclassMutableDefaultList).dump(DataclassMutableDefaultList()) == '{"xs": []}'

    def test_mutable_default_dict(self):
        assert JsonSerializer(DataclassMutableDefaultDict).dump(DataclassMutableDefaultDict()) == '{"xs": {}}'


class TestDecoder:
    def test_list(self):
        actual = JsonSerializer(DataclassWithList).load('{"xs": [1]}')
        expected = DataclassWithList([1])
        assert (actual == expected)

    def test_list_str(self):
        actual = JsonSerializer(DataclassWithListStr).load('{"xs": ["1"]}')
        expected = DataclassWithListStr(["1"])
        assert actual == expected

    def test_dict(self):
        actual = JsonSerializer(DataclassWithDict).load('{"kvs": {"1": "a"}}')
        expected = DataclassWithDict({'1': 'a'})
        assert actual == expected

    def test_dict_int(self):
        actual = JsonSerializer(DataclassWithDictInt).load('{"kvs": {"1": "a"}}')
        expected = DataclassWithDictInt({1: 'a'})
        assert actual == expected

    def test_set(self):
        actual = JsonSerializer(DataclassWithSet).load('{"xs": [1]}')
        expected = DataclassWithSet({1})
        assert actual == expected

    def test_tuple(self):
        actual = JsonSerializer(DataclassWithTuple).load('{"xs": [1]}')
        expected = DataclassWithTuple((1,))
        assert actual == expected

    def test_frozenset(self):
        actual = JsonSerializer(DataclassWithFrozenSet).load('{"xs": [1]}')
        expected = DataclassWithFrozenSet(frozenset([1]))
        assert actual == expected

    def test_deque(self):
        actual = JsonSerializer(DataclassWithDeque).load('{"xs": [1]}')
        expected = DataclassWithDeque(deque([1]))
        assert (actual == expected)

    def test_optional(self):
        actual1 = JsonSerializer(DataclassWithOptional).load('{"x": 1}')
        expected1 = DataclassWithOptional(1)
        assert actual1 == expected1

        actual2 = JsonSerializer(DataclassWithOptional).load('{"x": null}')
        expected2 = DataclassWithOptional(None)
        assert actual2 == expected2

    def test_optional_str(self):
        actual1 = JsonSerializer(DataclassWithOptionalStr).load('{"x": "1"}')
        expected1 = DataclassWithOptionalStr("1")
        assert actual1 == expected1

        actual2 = JsonSerializer(DataclassWithOptionalStr).load('{"x": null}')
        expected2 = DataclassWithOptionalStr(None)
        assert actual2 == expected2

        actual3 = JsonSerializer(DataclassWithOptionalStr, allow_missing=True).load('{}')
        expected3 = DataclassWithOptionalStr()
        assert actual3 == expected3

    def test_immutable_default(self):
        actual1 = JsonSerializer(DataclassIntImmutableDefault).load('{"x": 0}')
        expected1 = DataclassIntImmutableDefault()
        assert actual1 == expected1

    def test_mutable_default_list(self):
        expected = DataclassMutableDefaultList()

        actual1 = JsonSerializer(DataclassMutableDefaultList).load('{"xs": []}')
        assert actual1 == expected

        actual2 = JsonSerializer(DataclassMutableDefaultList, allow_missing=True).load('{}')
        assert actual2 == expected

    def test_mutable_default_dict(self):
        expected = DataclassMutableDefaultDict()

        actual1 = JsonSerializer(DataclassMutableDefaultDict).load('{"xs": {}}')
        assert actual1 == expected

        actual2 = JsonSerializer(DataclassMutableDefaultDict, allow_missing=True).load('{}')
        assert actual2 == expected
