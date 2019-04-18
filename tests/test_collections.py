from collections import deque

from serious.json import schema, Loading
from tests.entities import (DataClassIntImmutableDefault,
                            DataClassMutableDefaultDict,
                            DataClassMutableDefaultList, DataClassWithDeque,
                            DataClassWithDict, DataClassWithDictInt,
                            DataClassWithFrozenSet, DataClassWithList,
                            DataClassWithListStr, DataClassWithMyCollection,
                            DataClassWithOptional, DataClassWithOptionalStr,
                            DataClassWithSet, DataClassWithTuple,
                            DataClassWithUnionIntNone, MyCollection)

infer_missing = Loading(infer_missing=True)


class TestEncoder:
    def test_list(self):
        assert schema(DataClassWithList).dump(DataClassWithList([1])) == '{"xs": [1]}'

    def test_list_str(self):
        assert schema(DataClassWithListStr).dump(DataClassWithListStr(['1'])) == '{"xs": ["1"]}'

    def test_dict(self):
        assert schema(DataClassWithDict).dump(DataClassWithDict({'1': 'a'})) == '{"kvs": {"1": "a"}}'

    def test_dict_int(self):
        assert schema(DataClassWithDictInt).dump(DataClassWithDictInt({1: 'a'})) == '{"kvs": {"1": "a"}}'

    def test_set(self):
        assert schema(DataClassWithSet).dump(DataClassWithSet({1})) == '{"xs": [1]}'

    def test_tuple(self):
        assert schema(DataClassWithTuple).dump(DataClassWithTuple((1,))) == '{"xs": [1]}'

    def test_frozenset(self):
        assert schema(DataClassWithFrozenSet).dump(DataClassWithFrozenSet(frozenset([1]))) == '{"xs": [1]}'

    def test_deque(self):
        assert schema(DataClassWithDeque).dump(DataClassWithDeque(deque([1]))) == '{"xs": [1]}'

    def test_optional(self):
        s = schema(DataClassWithOptional)
        assert s.dump(DataClassWithOptional(1)) == '{"x": 1}'
        assert s.dump(DataClassWithOptional(None)) == '{"x": null}'

    def test_optional_str(self):
        s = schema(DataClassWithOptionalStr)
        assert s.dump(DataClassWithOptionalStr('1')) == '{"x": "1"}'
        assert s.dump(DataClassWithOptionalStr(None)) == '{"x": null}'
        assert s.dump(DataClassWithOptionalStr()) == '{"x": null}'

    def test_union_int_none(self):
        s = schema(DataClassWithUnionIntNone)
        assert s.dump(DataClassWithUnionIntNone(1)) == '{"x": 1}'
        assert s.dump(DataClassWithUnionIntNone(None)) == '{"x": null}'

    def test_my_collection(self):
        assert schema(DataClassWithMyCollection).dump(DataClassWithMyCollection(MyCollection([1]))) == '{"xs": [1]}'

    def test_immutable_default(self):
        assert schema(DataClassIntImmutableDefault).dump(DataClassIntImmutableDefault()) == '{"x": 0}'

    def test_mutable_default_list(self):
        assert schema(DataClassMutableDefaultList).dump(DataClassMutableDefaultList()) == '{"xs": []}'

    def test_mutable_default_dict(self):
        assert schema(DataClassMutableDefaultDict).dump(DataClassMutableDefaultDict()) == '{"xs": {}}'


class TestDecoder:
    def test_list(self):
        actual = schema(DataClassWithList).load('{"xs": [1]}')
        expected = DataClassWithList([1])
        assert (actual == expected)

    def test_list_str(self):
        actual = schema(DataClassWithListStr).load('{"xs": ["1"]}')
        expected = DataClassWithListStr(["1"])
        assert actual == expected

    def test_dict(self):
        actual = schema(DataClassWithDict).load('{"kvs": {"1": "a"}}')
        expected = DataClassWithDict({'1': 'a'})
        assert actual == expected

    def test_dict_int(self):
        actual = schema(DataClassWithDictInt).load('{"kvs": {"1": "a"}}')
        expected = DataClassWithDictInt({1: 'a'})
        assert actual == expected

    def test_set(self):
        actual = schema(DataClassWithSet).load('{"xs": [1]}')
        expected = DataClassWithSet({1})
        assert actual == expected

    def test_tuple(self):
        actual = schema(DataClassWithTuple).load('{"xs": [1]}')
        expected = DataClassWithTuple((1,))
        assert actual == expected

    def test_frozenset(self):
        actual = schema(DataClassWithFrozenSet).load('{"xs": [1]}')
        expected = DataClassWithFrozenSet(frozenset([1]))
        assert actual == expected

    def test_deque(self):
        actual = schema(DataClassWithDeque).load('{"xs": [1]}')
        expected = DataClassWithDeque(deque([1]))
        assert (actual == expected)

    def test_optional(self):
        actual1 = schema(DataClassWithOptional).load('{"x": 1}')
        expected1 = DataClassWithOptional(1)
        assert actual1 == expected1

        actual2 = schema(DataClassWithOptional).load('{"x": null}')
        expected2 = DataClassWithOptional(None)
        assert actual2 == expected2

    def test_optional_str(self):
        actual1 = schema(DataClassWithOptionalStr).load('{"x": "1"}')
        expected1 = DataClassWithOptionalStr("1")
        assert actual1 == expected1

        actual2 = schema(DataClassWithOptionalStr).load('{"x": null}')
        expected2 = DataClassWithOptionalStr(None)
        assert actual2 == expected2

        actual3 = schema(DataClassWithOptionalStr, load=infer_missing).load('{}')
        expected3 = DataClassWithOptionalStr()
        assert actual3 == expected3

    def test_my_collection(self):
        actual = schema(DataClassWithMyCollection).load('{"xs": [1]}')
        expected = DataClassWithMyCollection(MyCollection([1]))
        assert actual == expected

    def test_immutable_default(self):
        actual1 = schema(DataClassIntImmutableDefault).load('{"x": 0}')
        expected1 = DataClassIntImmutableDefault()
        assert actual1 == expected1

    def test_mutable_default_list(self):
        expected = DataClassMutableDefaultList()

        actual1 = schema(DataClassMutableDefaultList).load('{"xs": []}')
        assert actual1 == expected

        actual2 = schema(DataClassMutableDefaultList, load=infer_missing).load('{}')
        assert actual2 == expected

    def test_mutable_default_dict(self):
        expected = DataClassMutableDefaultDict()

        actual1 = schema(DataClassMutableDefaultDict).load('{"kvs": {}}')
        assert actual1 == expected

        actual2 = schema(DataClassMutableDefaultDict, load=infer_missing).load('{}')
        assert actual2 == expected
